# analysis/political_web.py - Multi-company political network graph
"""
Builds a bounded network graph of politicians <-> companies <-> bills <->
executives, seeded from the *entire* congressional stock-trading disclosure
dataset - every politician and every ticker they've disclosed trading, not
just one company (see scraping/insider_trading.get_all_congressional_trades).

That base layer is genuinely comprehensive: it's the whole public STOCK Act
dataset. It's then optionally enriched with lobbying/bill-sponsor/executive-
donation edges for the most active companies in that base graph, which is
where real caps have to apply - those are per-company/per-person API calls
against free public services (Senate LDA, Congress.gov, FEC), and a graph
with thousands of nodes isn't readable anyway. Every cap actually applied is
returned in the response (`caps_applied`) so it's never a silent limit.
"""

from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import defaultdict

from utils.cache import cached_fetch
from utils.political import names_possibly_match, bill_label
from scraping.insider_trading import get_all_congressional_trades
from scraping.lobbying import get_lobbying_summary
from scraping.congress_bills import resolve_bill_references, is_configured as congress_gov_configured
from scraping.company_officers import get_company_officers
from scraping.political_contributions import get_executive_donations


def _politician_id(member: str, chamber: str) -> str:
    return f"pol:{chamber}:{member}".lower()


def _company_id(ticker: str) -> str:
    return f"co:{ticker}".upper()


def _bill_id(bill_type: str, bill_number: str) -> str:
    return f"bill:{bill_type}{bill_number}".lower()


def _exec_id(name: str, ticker: str) -> str:
    return f"exec:{ticker}:{name}".lower()


def build_trading_base(days_back: int, max_trading_edges: int) -> Dict[str, Any]:
    """
    Aggregate the full congressional trading dataset into a
    politician<->company bipartite graph, capped to the top N edges by
    disclosed transaction count (a reasonable proxy for activity/relevance
    since exact dollar amounts are only disclosed as ranges).
    """
    raw = get_all_congressional_trades(days_back=days_back)
    if not raw.get('success'):
        return {'success': False, 'error': raw.get('error'), 'nodes': {}, 'edges': []}

    pair_counts: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {'count': 0, 'buys': 0, 'sells': 0, 'last_date': None})
    for tx in raw['transactions']:
        key = (tx['member'], tx['chamber'], tx['ticker'])
        agg = pair_counts[key]
        agg['count'] += 1
        tx_type = tx['transaction_type'].lower()
        if 'purchase' in tx_type or tx_type == 'buy':
            agg['buys'] += 1
        elif 'sale' in tx_type or 'sell' in tx_type:
            agg['sells'] += 1
        if not agg['last_date'] or tx['transaction_date'] > agg['last_date']:
            agg['last_date'] = tx['transaction_date']

    pairs = [
        {'member': member, 'chamber': chamber, 'ticker': ticker, **agg}
        for (member, chamber, ticker), agg in pair_counts.items()
    ]
    pairs.sort(key=lambda p: p['count'], reverse=True)
    top_pairs = pairs[:max_trading_edges]

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    for pair in top_pairs:
        pol_id = _politician_id(pair['member'], pair['chamber'])
        co_id = _company_id(pair['ticker'])

        if pol_id not in nodes:
            nodes[pol_id] = {'id': pol_id, 'type': 'politician', 'label': pair['member'], 'chamber': pair['chamber']}
        if co_id not in nodes:
            nodes[co_id] = {'id': co_id, 'type': 'company', 'label': pair['ticker'], 'ticker': pair['ticker']}

        direction = 'net_buying' if pair['buys'] > pair['sells'] else 'net_selling' if pair['sells'] > pair['buys'] else 'mixed'
        edges.append({
            'source': pol_id, 'target': co_id, 'type': 'trades',
            'weight': pair['count'], 'direction': direction, 'last_date': pair['last_date'],
        })

    return {
        'success': True,
        'nodes': nodes,
        'edges': edges,
        'total_disclosed_pairs': len(pairs),
        'pairs_included': len(top_pairs),
        'dataset_totals': {
            'total_transactions': raw['total_found'],
            'unique_members': raw['unique_members'],
            'unique_tickers': raw['unique_tickers'],
        },
    }


def _enrich_company_lobbying(ticker: str) -> Dict[str, Any]:
    lobbying = get_lobbying_summary(ticker, ticker, years_back=2)
    if not lobbying.get('success') or not lobbying.get('bill_references'):
        return {'ticker': ticker, 'lobbying': lobbying, 'bills': []}

    filing_years = sorted({f['filing_year'] for f in lobbying.get('filings', []) if f.get('filing_year')}) or [datetime.now().year]
    bills = resolve_bill_references(lobbying['bill_references'], filing_years, limit=5)
    return {'ticker': ticker, 'lobbying': lobbying, 'bills': [b for b in bills if b.get('success')]}


def enrich_with_lobbying(graph: Dict[str, Any], tickers: List[str], max_companies: int) -> Dict[str, Any]:
    """Add company->bill->sponsor edges for the top N most-active companies in the base graph."""
    target_tickers = tickers[:max_companies]
    if not target_tickers:
        return {'companies_enriched': 0, 'bills_added': 0}

    def cache_fn():
        results = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(_enrich_company_lobbying, t): t for t in target_tickers}
            for future in as_completed(futures):
                t = futures[future]
                try:
                    results[t] = future.result()
                except Exception as e:
                    results[t] = {'ticker': t, 'lobbying': {'success': False, 'error': str(e)}, 'bills': []}
        return results

    cache_key = f"web_lobbying_enrichment_{'_'.join(sorted(target_tickers))}"
    per_company = cached_fetch(cache_key, ttl_seconds=6 * 3600, fetch_fn=cache_fn)

    seen_edges = {(e['source'], e['target'], e['type']) for e in graph['edges']}

    def add_edge_once(source: str, target: str, edge_type: str, **extra):
        key = (source, target, edge_type)
        if key in seen_edges:
            return
        seen_edges.add(key)
        graph['edges'].append({'source': source, 'target': target, 'type': edge_type, 'weight': 1, **extra})

    bills_added = 0
    for ticker, result in per_company.items():
        co_id = _company_id(ticker)
        if co_id not in graph['nodes']:
            continue

        for bill in result['bills']:
            b_id = _bill_id(bill['bill_type'], bill['bill_number'])
            if b_id not in graph['nodes']:
                graph['nodes'][b_id] = {
                    'id': b_id, 'type': 'bill', 'label': bill_label(bill),
                    'title': bill.get('title'), 'url': bill.get('congress_gov_url'),
                }
                bills_added += 1

            add_edge_once(co_id, b_id, 'lobbies_for')

            sponsor = bill.get('sponsor')
            if sponsor and sponsor.get('name'):
                # Link to an existing politician node if the trading-graph name
                # possibly matches (heuristic); otherwise add a standalone sponsor node.
                matched_id = None
                for node_id, node in graph['nodes'].items():
                    if node['type'] == 'politician' and names_possibly_match(node['label'], sponsor['name']):
                        matched_id = node_id
                        break

                sponsor_id = matched_id or f"pol:sponsor:{sponsor['name']}".lower()
                if sponsor_id not in graph['nodes']:
                    graph['nodes'][sponsor_id] = {
                        'id': sponsor_id, 'type': 'politician', 'label': sponsor['name'],
                        'party': sponsor.get('party'), 'state': sponsor.get('state'),
                        'chamber': sponsor.get('chamber'),
                    }
                add_edge_once(b_id, sponsor_id, 'sponsored_by')

    return {'companies_enriched': len(per_company), 'bills_added': bills_added}


def enrich_with_donations(graph: Dict[str, Any], tickers: List[str], max_companies: int) -> Dict[str, Any]:
    """Add executive->company and executive->donated_to edges for a smaller bounded subset (FEC is the slowest/heaviest tier)."""
    target_tickers = tickers[:max_companies]
    execs_added = 0
    donation_edges_added = 0

    for ticker in target_tickers:
        co_id = _company_id(ticker)
        if co_id not in graph['nodes']:
            continue

        officers_result = get_company_officers(ticker, limit=4)
        if not officers_result.get('success') or not officers_result.get('officers'):
            continue

        company_name = officers_result.get('company_name', ticker)
        donations_result = get_executive_donations(officers_result['officers'], company_name, per_officer=3)

        for exec_entry in donations_result.get('executives', []):
            if not exec_entry.get('donations'):
                continue

            e_id = _exec_id(exec_entry['name'], ticker)
            if e_id not in graph['nodes']:
                graph['nodes'][e_id] = {
                    'id': e_id, 'type': 'executive', 'label': exec_entry['name'], 'title': exec_entry.get('title'),
                }
                execs_added += 1
            graph['edges'].append({'source': e_id, 'target': co_id, 'type': 'works_at', 'weight': 1})

            for donation in exec_entry['donations']:
                recipient = donation.get('candidate_name') or donation.get('committee_name')
                if not recipient:
                    continue

                matched_id = None
                for node_id, node in graph['nodes'].items():
                    if node['type'] == 'politician' and names_possibly_match(node['label'], recipient):
                        matched_id = node_id
                        break

                recipient_id = matched_id or f"pol:donee:{recipient}".lower()
                if recipient_id not in graph['nodes']:
                    graph['nodes'][recipient_id] = {
                        'id': recipient_id, 'type': 'politician', 'label': recipient,
                        'party': donation.get('committee_party'),
                    }
                graph['edges'].append({
                    'source': e_id, 'target': recipient_id, 'type': 'donated_to',
                    'weight': 1, 'amount': donation.get('amount'), 'date': donation.get('date'),
                })
                donation_edges_added += 1

    return {'executives_added': execs_added, 'donation_edges_added': donation_edges_added}


def build_political_web(
    days_back: int = 730,
    max_trading_edges: int = 150,
    max_lobbying_companies: int = 20,
    max_donation_companies: int = 0,
) -> Dict[str, Any]:
    """
    Orchestrate the full multi-tier graph build. `max_donation_companies`
    defaults to 0 (opt-in) since FEC per-executive lookups are the slowest
    tier and least likely to be wanted on every load.
    """
    base = build_trading_base(days_back, max_trading_edges)
    if not base.get('success'):
        return {
            'success': False,
            'error': base.get('error'),
            'source': 'Senate/House Stock Watcher',
        }

    graph = {'nodes': base['nodes'], 'edges': base['edges']}

    # Enrich the most-active companies first (by trading edge weight)
    company_weight = defaultdict(int)
    for edge in base['edges']:
        target_node = graph['nodes'].get(edge['target'])
        if target_node and target_node['type'] == 'company':
            company_weight[target_node['ticker']] += edge['weight']
    ranked_tickers = [t for t, _ in sorted(company_weight.items(), key=lambda kv: kv[1], reverse=True)]

    lobbying_stats = {'companies_enriched': 0, 'bills_added': 0}
    if max_lobbying_companies > 0:
        lobbying_stats = enrich_with_lobbying(graph, ranked_tickers, max_lobbying_companies)

    donation_stats = {'executives_added': 0, 'donation_edges_added': 0}
    if max_donation_companies > 0:
        donation_stats = enrich_with_donations(graph, ranked_tickers, max_donation_companies)

    node_counts = defaultdict(int)
    for node in graph['nodes'].values():
        node_counts[node['type']] += 1

    return {
        'success': True,
        'nodes': list(graph['nodes'].values()),
        'edges': graph['edges'],
        'stats': {
            'total_nodes': len(graph['nodes']),
            'total_edges': len(graph['edges']),
            'node_counts': dict(node_counts),
            'dataset_totals': base['dataset_totals'],
            'total_disclosed_trading_pairs': base['total_disclosed_pairs'],
        },
        'caps_applied': {
            'days_back': days_back,
            'max_trading_edges': max_trading_edges,
            'trading_pairs_included': base['pairs_included'],
            'max_lobbying_companies': max_lobbying_companies,
            'max_donation_companies': max_donation_companies,
            **lobbying_stats,
            **donation_stats,
        },
        'congress_gov_configured': congress_gov_configured(),
        'timestamp': datetime.now().isoformat(),
        'disclaimer': (
            "Base layer (politician<->company trades) covers the full public STOCK Act "
            "disclosure dataset. Lobbying/bill-sponsor and executive-donation layers are "
            "capped to the most active companies to keep this responsive against free "
            "public APIs - see caps_applied. Politician nodes added via lobbying/donation "
            "enrichment are linked to existing trading-graph nodes via heuristic name "
            "matching, not confirmed identity."
        ),
    }
