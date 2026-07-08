# scraping/geopolitical.py - Geopolitical trend & risk scraper
"""
Uses the GDELT Project's free, key-free DOC 2.0 API to find recent global news
coverage linking a company/ticker to geopolitical risk themes (tariffs,
sanctions, export controls, war/conflict, elections, central bank policy,
regulation). GDELT indexes worldwide news coverage in near-real time.

Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

import requests
from typing import Dict, List, Any
from datetime import datetime
import time

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

GEOPOLITICAL_THEMES = {
    'trade_policy': ['tariff', 'trade war', 'export ban', 'export controls', 'import restriction'],
    'sanctions': ['sanctions', 'embargo', 'export controls'],
    'conflict': ['war', 'military conflict', 'invasion', 'geopolitical tension'],
    'elections_policy': ['election', 'regulation', 'antitrust', 'policy change'],
    'monetary_policy': ['central bank', 'interest rate', 'federal reserve', 'inflation policy'],
    'supply_chain': ['supply chain', 'chip shortage', 'semiconductor restriction'],
}

_HEADERS = {'User-Agent': 'Sentilyze Personal Use (geopolitical risk dashboard)'}


def get_geopolitical_context(ticker: str, company_name: str = "") -> Dict[str, Any]:
    """
    Search recent global news for geopolitical coverage mentioning the company,
    grouped by risk theme (trade policy, sanctions, conflict, elections/policy,
    monetary policy, supply chain). Article tone/sentiment is scored downstream
    by the ML sentiment engine, not by GDELT's own (coarser) tone metric.
    """
    ticker = ticker.upper().strip()
    subject = company_name or ticker

    themes_found: Dict[str, List[Dict[str, Any]]] = {}
    errors = []

    try:
        for theme, keywords in GEOPOLITICAL_THEMES.items():
            keyword_clause = " OR ".join(f'"{kw}"' for kw in keywords)
            query = f'"{subject}" ({keyword_clause}) sourcelang:english'

            params = {
                'query': query,
                'mode': 'ArtList',
                'maxrecords': 10,
                'format': 'json',
                'sort': 'DateDesc',
                'timespan': '1month',
            }

            try:
                resp = requests.get(GDELT_DOC_URL, params=params, headers=_HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                articles = data.get('articles', [])
                if articles:
                    themes_found[theme] = [
                        {
                            'title': a.get('title', ''),
                            'url': a.get('url', ''),
                            'source': a.get('domain', ''),
                            'published': a.get('seendate', ''),
                            'language': a.get('language', ''),
                        }
                        for a in articles[:5]
                    ]
            except (requests.RequestException, ValueError) as theme_error:
                errors.append(f"{theme}: {str(theme_error)}")

            time.sleep(0.3)  # be polite to GDELT's shared public endpoint

        total_articles = sum(len(v) for v in themes_found.values())
        exposure_level = 'low'
        if total_articles >= 15:
            exposure_level = 'high'
        elif total_articles >= 5:
            exposure_level = 'moderate'

        return {
            'success': True,
            'ticker': ticker,
            'subject_searched': subject,
            'themes': themes_found,
            'total_articles': total_articles,
            'geopolitical_exposure': exposure_level,
            'partial_errors': errors,
            'timestamp': datetime.now().isoformat(),
            'source': 'GDELT Project DOC 2.0 API',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching geopolitical context for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'GDELT Project DOC 2.0 API',
        }


if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"Testing geopolitical scraper for {test_ticker}...")
    result = get_geopolitical_context(test_ticker, "Apple")
    if result['success']:
        print(f"Exposure: {result['geopolitical_exposure']}, {result['total_articles']} articles across themes")
    else:
        print(f"Failed: {result['error']}")
