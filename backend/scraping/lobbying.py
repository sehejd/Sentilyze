# scraping/lobbying.py - Federal lobbying disclosure scraper
"""
Pulls real corporate lobbying activity from the Senate's Lobbying Disclosure
Act (LDA) API - public, free, no API key required (anonymous clients are
just subject to stricter rate throttling than registered ones).

Docs: https://lda.senate.gov/api/redoc/v1/

Each LD-2 quarterly filing lists "lobbying activities": a general issue area
code (e.g. TAX, HCR, TAR) plus a free-text `specific_issues` description that
frequently references specific bills by number (e.g. "H.R. 1234", "S. 567").
We extract those references so they can be cross-referenced against
Congress.gov for sponsor/status details.
"""

import re
import requests
from typing import Dict, List, Any
from datetime import datetime

from utils.cache import cached_fetch

LDA_BASE_URL = "https://lda.senate.gov/api/v1"
_HEADERS = {'User-Agent': 'Sentilyze Personal Use (lobbying disclosure dashboard)'}

# Matches "H.R. 1234", "HR 1234", "H.R.1234", "S. 567", "S 567", "S.J.Res. 12", etc.
_BILL_REF_PATTERN = re.compile(
    r'\b(H\.?\s?R\.?|S\.?|H\.?\s?J\.?\s?Res\.?|S\.?\s?J\.?\s?Res\.?|'
    r'H\.?\s?Con\.?\s?Res\.?|S\.?\s?Con\.?\s?Res\.?|H\.?\s?Res\.?|S\.?\s?Res\.?)\s?(\d{1,5})\b',
    re.IGNORECASE,
)

_BILL_TYPE_MAP = {
    'hr': 'hr', 'h.r': 'hr',
    's': 's',
    'hjres': 'hjres', 'h.j.res': 'hjres',
    'sjres': 'sjres', 's.j.res': 'sjres',
    'hconres': 'hconres', 'h.con.res': 'hconres',
    'sconres': 'sconres', 's.con.res': 'sconres',
    'hres': 'hres', 'h.res': 'hres',
    'sres': 'sres', 's.res': 'sres',
}


def _normalize_bill_type(raw: str) -> str:
    cleaned = re.sub(r'[\s.]', '', raw).lower()
    return _BILL_TYPE_MAP.get(cleaned, cleaned)


def extract_bill_references(text: str) -> List[Dict[str, str]]:
    """Extract distinct bill references (e.g. {'bill_type': 'hr', 'number': '1234'}) from free text."""
    if not text:
        return []

    seen = set()
    refs = []
    for match in _BILL_REF_PATTERN.finditer(text):
        bill_type = _normalize_bill_type(match.group(1))
        number = match.group(2)
        key = f"{bill_type}{number}"
        if key not in seen:
            seen.add(key)
            refs.append({'bill_type': bill_type, 'number': number, 'raw': match.group(0)})
    return refs


def _fetch_filings_page(params: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.get(f"{LDA_BASE_URL}/filings/", params=params, headers=_HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()


def search_lobbying_filings(company_name: str, filing_years: List[int], max_pages: int = 2) -> Dict[str, Any]:
    """
    Search LD-2 filings where the lobbying client matches company_name, across
    the given filing years. Cached per (company_name, years) for a few hours
    since disclosure filings only update quarterly.
    """
    cache_key = f"lda_filings_{company_name}_{'-'.join(map(str, filing_years))}"

    def fetch():
        all_filings = []
        for year in filing_years:
            page = 1
            while page <= max_pages:
                data = _fetch_filings_page({
                    'client_name': company_name,
                    'filing_year': year,
                    'page': page,
                    'page_size': 25,
                })
                results = data.get('results', [])
                all_filings.extend(results)
                if not data.get('next'):
                    break
                page += 1
        return all_filings

    try:
        return {
            'success': True,
            'filings': cached_fetch(cache_key, ttl_seconds=6 * 3600, fetch_fn=fetch),
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'filings': []}


def get_lobbying_summary(ticker: str, company_name: str, years_back: int = 2) -> Dict[str, Any]:
    """
    Aggregate a company's recent federal lobbying activity: total filings,
    estimated spend, top issue areas, lobbying firms retained, and every
    distinct bill referenced in the filings' specific-issues text.
    """
    ticker = ticker.upper().strip()
    current_year = datetime.now().year
    years = list(range(current_year - years_back + 1, current_year + 1))

    result = search_lobbying_filings(company_name, years)
    if not result['success']:
        return {
            'success': False,
            'error': f"Error fetching lobbying data for {company_name}: {result['error']}",
            'source': 'Senate LDA API',
        }

    filings = result['filings']
    if not filings:
        return {
            'success': True,
            'ticker': ticker,
            'company_name': company_name,
            'total_filings': 0,
            'estimated_total_spend': 0,
            'registrants': [],
            'issue_areas': {},
            'bill_references': [],
            'filings': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'Senate LDA API',
        }

    registrants = set()
    issue_areas: Dict[str, int] = {}
    all_bill_refs: Dict[str, Dict[str, Any]] = {}
    total_spend = 0.0
    filing_summaries = []

    for filing in filings:
        registrant_name = (filing.get('registrant') or {}).get('name')
        if registrant_name:
            registrants.add(registrant_name)

        income = filing.get('income')
        expenses = filing.get('expenses')
        amount = income or expenses
        if amount:
            try:
                total_spend += float(amount)
            except (TypeError, ValueError):
                pass

        activities = filing.get('lobbying_activities', []) or []
        filing_bill_refs = []
        for activity in activities:
            issue_code = activity.get('general_issue_code_display') or activity.get('general_issue_code')
            if issue_code:
                issue_areas[issue_code] = issue_areas.get(issue_code, 0) + 1

            specific_issues = activity.get('specific_issues', '') or ''
            for ref in extract_bill_references(specific_issues):
                key = f"{ref['bill_type']}{ref['number']}"
                filing_bill_refs.append(key)
                if key not in all_bill_refs:
                    all_bill_refs[key] = {**ref, 'mentions': 0, 'issue_areas': set()}
                all_bill_refs[key]['mentions'] += 1
                if issue_code:
                    all_bill_refs[key]['issue_areas'].add(issue_code)

        filing_summaries.append({
            'filing_uuid': filing.get('filing_uuid'),
            'registrant': registrant_name,
            'filing_year': filing.get('filing_year'),
            'filing_period': filing.get('filing_period_display') or filing.get('filing_period'),
            'amount': amount,
            'bill_references': filing_bill_refs,
            'dt_posted': filing.get('dt_posted'),
        })

    bill_list = [
        {**v, 'issue_areas': sorted(v['issue_areas'])}
        for v in all_bill_refs.values()
    ]
    bill_list.sort(key=lambda b: b['mentions'], reverse=True)

    return {
        'success': True,
        'ticker': ticker,
        'company_name': company_name,
        'total_filings': len(filings),
        'estimated_total_spend': round(total_spend, 2),
        'registrants': sorted(registrants),
        'issue_areas': dict(sorted(issue_areas.items(), key=lambda kv: kv[1], reverse=True)),
        'bill_references': bill_list,
        'filings': filing_summaries[:25],
        'timestamp': datetime.now().isoformat(),
        'source': 'Senate LDA API (lda.senate.gov)',
    }


if __name__ == "__main__":
    summary = get_lobbying_summary("AAPL", "Apple Inc.")
    print(summary.get('total_filings'), summary.get('bill_references'))
