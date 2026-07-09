# analysis/political_network.py - "Deeper dive" political network builder
"""
Ties together four public-disclosure data sources into one picture of who's
connected to whom around a company:

  1. What the company lobbies for (Senate LDA filings -> scraping/lobbying.py)
  2. What those lobbied bills are, and who sponsors them (Congress.gov -> scraping/congress_bills.py)
  3. Who the company's named executives are (yfinance -> scraping/company_officers.py)
  4. What politicians those executives personally donate to (FEC -> scraping/political_contributions.py)

...then cross-references:
  - Does a bill's sponsor also show up in the congressional stock-trading
    data (scraping/insider_trading.py) for this same ticker?
  - Did a company executive donate to a politician who sponsors a bill the
    company lobbies on?

Name matching across these sources is heuristic (data sources format names
differently - "Cruz, Ted" vs "Ted Cruz" vs "Rafael Edward Cruz"), so
connections are surfaced as "possible matches for manual verification," not
asserted as certain.
"""

from typing import Dict, Any, List
from datetime import datetime

from scraping.lobbying import get_lobbying_summary
from scraping.congress_bills import resolve_bill_references, is_configured as congress_gov_configured
from scraping.company_officers import get_company_officers
from scraping.political_contributions import get_executive_donations
from scraping.insider_trading import get_congressional_trades
from utils.political import names_possibly_match as _names_possibly_match, bill_label as _bill_label


def build_political_network(ticker: str, company_name: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()

    lobbying = get_lobbying_summary(ticker, company_name)
    officers = get_company_officers(ticker)
    congressional_trades = get_congressional_trades(ticker)

    bills: List[Dict[str, Any]] = []
    if lobbying.get('success') and lobbying.get('bill_references'):
        filing_years = sorted({f['filing_year'] for f in lobbying.get('filings', []) if f.get('filing_year')}) or [datetime.now().year]
        bills = resolve_bill_references(lobbying['bill_references'], filing_years, limit=8)
        # attach the original mention/issue-area context back onto resolved bills
        ref_context = {f"{b['bill_type']}{b['number']}": b for b in lobbying['bill_references']}
        for bill in bills:
            key = f"{bill.get('bill_type')}{bill.get('bill_number')}"
            context = ref_context.get(key, {})
            bill['mentions'] = context.get('mentions')
            bill['issue_areas'] = context.get('issue_areas')

    donations = None
    if officers.get('success') and officers.get('officers'):
        donations = get_executive_donations(officers['officers'], company_name)

    connections: List[Dict[str, Any]] = []

    trader_names = []
    if congressional_trades.get('success'):
        trader_names = list({tx['member'] for tx in congressional_trades.get('transactions', [])})

    for bill in bills:
        sponsor = bill.get('sponsor')
        if not sponsor or not sponsor.get('name'):
            continue

        for trader_name in trader_names:
            if _names_possibly_match(sponsor['name'], trader_name):
                connections.append({
                    'type': 'bill_sponsor_trades_stock',
                    'description': (
                        f"{sponsor['name']} ({sponsor.get('party', '?')}-{sponsor.get('state', '?')}) sponsors "
                        f"{_bill_label(bill)} ({bill.get('title', 'untitled')}), "
                        f"a bill {company_name} lobbies on, and also appears in {ticker}'s congressional trading disclosures."
                    ),
                    'bill': _bill_label(bill),
                    'sponsor': sponsor['name'],
                    'trader_name': trader_name,
                    'confidence': 'heuristic_name_match',
                })

        if donations:
            for exec_entry in donations.get('executives', []):
                for donation in exec_entry.get('donations', []):
                    recipient = donation.get('candidate_name') or donation.get('committee_name')
                    if recipient and _names_possibly_match(sponsor['name'], recipient):
                        connections.append({
                            'type': 'executive_donated_to_bill_sponsor',
                            'description': (
                                f"{exec_entry['name']} ({exec_entry.get('title', 'executive')} at {company_name}) "
                                f"made a ${donation.get('amount', '?')} contribution to {recipient}, who possibly "
                                f"matches {sponsor['name']}, sponsor of {_bill_label(bill)} "
                                f"- a bill {company_name} lobbies on."
                            ),
                            'executive': exec_entry['name'],
                            'bill': _bill_label(bill),
                            'sponsor': sponsor['name'],
                            'donation_amount': donation.get('amount'),
                            'donation_date': donation.get('date'),
                            'confidence': 'heuristic_name_match',
                        })

    return {
        'ticker': ticker,
        'company_name': company_name,
        'lobbying': lobbying,
        'bills': bills,
        'officers': officers,
        'executive_donations': donations,
        'connections': connections,
        'congress_gov_configured': congress_gov_configured(),
        'timestamp': datetime.now().isoformat(),
        'disclaimer': (
            "All data is drawn from public federal disclosures (Senate LDA lobbying filings, "
            "Congress.gov, STOCK Act congressional trading reports, and FEC campaign finance records). "
            "Name-based connections are heuristic matches for manual verification, not confirmed links."
        ),
    }
