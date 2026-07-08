# scraping/company_officers.py - Named company executives
"""
Pulls named corporate officers (CEO, CFO, etc.) from yfinance, which surfaces
the `companyOfficers` array Yahoo Finance sources from company filings/proxy
statements. Used as the "prominent figures" side of the political network
deeper-dive (analysis/political_network.py) - these names are what we search
for in FEC campaign contribution records.
"""

from typing import Dict, Any, List
from datetime import datetime
import yfinance as yf


def get_company_officers(ticker: str, limit: int = 8) -> Dict[str, Any]:
    ticker = ticker.upper().strip()

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        return {'success': False, 'error': f"Error fetching officers for {ticker}: {str(e)}", 'source': 'yfinance'}

    raw_officers = info.get('companyOfficers') or []
    if not raw_officers:
        return {
            'success': True, 'ticker': ticker, 'officers': [],
            'note': 'No officer data available for this ticker',
            'source': 'yfinance',
        }

    officers: List[Dict[str, Any]] = []
    for officer in raw_officers:
        name = officer.get('name')
        if not name:
            continue
        officers.append({
            'name': name,
            'title': officer.get('title'),
            'age': officer.get('age'),
            'total_pay': officer.get('totalPay'),
            'year_born': officer.get('yearBorn'),
        })

    # Prioritize C-suite/exec titles, then by pay
    def rank(o):
        title = (o.get('title') or '').lower()
        is_exec = any(t in title for t in ['chief', 'president', 'chair', 'founder'])
        return (0 if is_exec else 1, -(o.get('total_pay') or 0))

    officers.sort(key=rank)

    return {
        'success': True,
        'ticker': ticker,
        'company_name': info.get('longName', ticker),
        'officers': officers[:limit],
        'timestamp': datetime.now().isoformat(),
        'source': 'yfinance (sourced from company filings/proxy statements)',
    }


if __name__ == "__main__":
    result = get_company_officers("AAPL")
    print(result.get('officers'))
