# scraping/sec_edgar.py - SEC EDGAR fundamentals + quarterly/annual report scraper
"""
Pulls real fundamental data straight from SEC filings via EDGAR's public,
key-free APIs:

- https://www.sec.gov/files/company_tickers.json          ticker -> CIK map
- https://data.sec.gov/submissions/CIK##########.json      filing history (10-Q/10-K)
- https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json   as-reported XBRL facts

SEC requires a descriptive User-Agent with contact info on every request
(https://www.sec.gov/os/webmaster-faq#developers) - set SEC_EDGAR_USER_AGENT
in the environment. Requests are cached on disk since the ticker map and
filing history rarely change within a day.
"""

import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.cache import cached_fetch

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# us-gaap XBRL concepts we care about, in priority order (companies tag things
# slightly differently, so we fall back through the list per metric)
FUNDAMENTAL_CONCEPTS = {
    'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                'RevenueFromContractWithCustomerIncludingAssessedTax', 'SalesRevenueNet'],
    'net_income': ['NetIncomeLoss', 'ProfitLoss'],
    'eps_diluted': ['EarningsPerShareDiluted'],
    'eps_basic': ['EarningsPerShareBasic'],
    'gross_profit': ['GrossProfit'],
    'operating_income': ['OperatingIncomeLoss'],
    'total_assets': ['Assets'],
    'total_liabilities': ['Liabilities'],
    'stockholders_equity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'cash_and_equivalents': ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'],
    'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
    'current_assets': ['AssetsCurrent'],
    'current_liabilities': ['LiabilitiesCurrent'],
    'long_term_debt': ['LongTermDebtNoncurrent', 'LongTermDebt'],
}


def _headers() -> Dict[str, str]:
    ua = os.getenv('SEC_EDGAR_USER_AGENT', 'Sentilyze Personal-Use App (contact: unset@example.com)')
    return {'User-Agent': ua, 'Accept-Encoding': 'gzip, deflate'}


def get_cik_for_ticker(ticker: str) -> Optional[str]:
    """Resolve a ticker symbol to a 10-digit zero-padded CIK string."""
    ticker = ticker.upper().strip()

    def fetch_map():
        resp = requests.get(TICKER_MAP_URL, headers=_headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()

    ticker_map = cached_fetch('sec_ticker_map', ttl_seconds=24 * 3600, fetch_fn=fetch_map)

    for entry in ticker_map.values():
        if entry.get('ticker', '').upper() == ticker:
            return str(entry['cik_str']).zfill(10)
    return None


def get_recent_filings(ticker: str, forms: Optional[List[str]] = None, limit: int = 8) -> Dict[str, Any]:
    """
    Get metadata for a company's most recent quarterly/annual reports (10-Q/10-K).
    Returns filing dates, accession numbers, and direct links to the filed document.
    """
    forms = forms or ['10-Q', '10-K']
    ticker = ticker.upper().strip()

    try:
        cik = get_cik_for_ticker(ticker)
        if not cik:
            return {'success': False, 'error': f'No SEC CIK found for ticker {ticker}', 'source': 'SEC EDGAR'}

        def fetch_submissions():
            resp = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=_headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()

        submissions = cached_fetch(f'sec_submissions_{cik}', ttl_seconds=6 * 3600, fetch_fn=fetch_submissions)

        recent = submissions.get('filings', {}).get('recent', {})
        forms_list = recent.get('form', [])
        accession_numbers = recent.get('accessionNumber', [])
        primary_docs = recent.get('primaryDocument', [])
        filing_dates = recent.get('filingDate', [])
        report_dates = recent.get('reportDate', [])

        filings = []
        for i, form in enumerate(forms_list):
            if form in forms:
                accession_clean = accession_numbers[i].replace('-', '')
                filings.append({
                    'form': form,
                    'filing_date': filing_dates[i] if i < len(filing_dates) else None,
                    'report_period': report_dates[i] if i < len(report_dates) else None,
                    'accession_number': accession_numbers[i],
                    'document_url': f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{primary_docs[i]}",
                    'filing_index_url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}",
                })
            if len(filings) >= limit:
                break

        return {
            'success': True,
            'ticker': ticker,
            'cik': cik,
            'company_name': submissions.get('name', ticker),
            'sic_description': submissions.get('sicDescription'),
            'filings': filings,
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC EDGAR',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching SEC filings for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC EDGAR',
        }


def get_company_facts(ticker: str) -> Dict[str, Any]:
    """
    Pull as-reported fundamental figures (revenue, net income, EPS, balance
    sheet items, cash flow) straight from XBRL data tagged in SEC filings.
    Returns the most recent annual (10-K) and quarterly (10-Q) values plus a
    short time series per metric for trend/growth calculations.
    """
    ticker = ticker.upper().strip()

    try:
        cik = get_cik_for_ticker(ticker)
        if not cik:
            return {'success': False, 'error': f'No SEC CIK found for ticker {ticker}', 'source': 'SEC EDGAR'}

        def fetch_facts():
            resp = requests.get(COMPANY_FACTS_URL.format(cik=cik), headers=_headers(), timeout=20)
            resp.raise_for_status()
            return resp.json()

        facts = cached_fetch(f'sec_facts_{cik}', ttl_seconds=6 * 3600, fetch_fn=fetch_facts)
        us_gaap = facts.get('facts', {}).get('us-gaap', {})

        metrics: Dict[str, Any] = {}
        for metric_name, concept_candidates in FUNDAMENTAL_CONCEPTS.items():
            series = None
            for concept in concept_candidates:
                if concept in us_gaap:
                    units = us_gaap[concept].get('units', {})
                    # EPS is USD/shares, everything else USD
                    unit_key = next(iter(units.keys()), None)
                    if unit_key:
                        series = units[unit_key]
                        break
            if not series:
                continue

            # Keep only 10-Q/10-K filed values, most recent first
            filtered = [v for v in series if v.get('form') in ('10-Q', '10-K')]
            filtered.sort(key=lambda v: v.get('end', ''), reverse=True)

            if filtered:
                metrics[metric_name] = {
                    'latest_value': filtered[0].get('val'),
                    'latest_period_end': filtered[0].get('end'),
                    'latest_form': filtered[0].get('form'),
                    'latest_fiscal_period': filtered[0].get('fp'),
                    'history': [
                        {'end': v.get('end'), 'val': v.get('val'), 'form': v.get('form'), 'fp': v.get('fp')}
                        for v in filtered[:8]
                    ],
                }

        return {
            'success': True,
            'ticker': ticker,
            'cik': cik,
            'entity_name': facts.get('entityName', ticker),
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC EDGAR XBRL',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching SEC company facts for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC EDGAR XBRL',
        }


if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"Testing SEC EDGAR scraper for {test_ticker}...")
    filings = get_recent_filings(test_ticker)
    print(filings)
    facts = get_company_facts(test_ticker)
    print(facts.get('metrics', {}).keys() if facts.get('success') else facts)
