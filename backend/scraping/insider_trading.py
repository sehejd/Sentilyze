# scraping/insider_trading.py - Congressional (political) insider trading scraper
"""
Pulls real, public STOCK Act disclosure data aggregated by two well-known
open-source projects (no API key required):

- Senate: https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json
- House:  https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json

These mirror the disclosures members of Congress are legally required to file
under the STOCK Act. Datasets are large (tens of MB) and only update daily, so
we cache them on disk.

We deliberately focus on political/congressional trading rather than
corporate Form 4 insider trades (execs/officers) because that's what the user
asked for ("insider trading metric, primarily political"); corporate Form 4
data is available from the same SEC EDGAR full-text search if extended later.
"""

import requests
from typing import Dict, List, Any
from datetime import datetime, timedelta

from utils.cache import cached_fetch

SENATE_URL = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"
HOUSE_URL = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"

_HEADERS = {'User-Agent': 'Sentilyze Personal Use (congressional trading dashboard)'}


def _fetch_json(url: str, cache_key: str) -> List[Dict[str, Any]]:
    def fetch():
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    return cached_fetch(cache_key, ttl_seconds=12 * 3600, fetch_fn=fetch)


def _normalize_ticker(raw: str) -> str:
    return (raw or '').upper().strip().lstrip('$')


def _parse_amount_range(amount_str: str) -> Dict[str, float]:
    """Disclosures report a dollar range like '$1,001 - $15,000', not an exact figure."""
    if not amount_str:
        return {'low': 0.0, 'high': 0.0}
    cleaned = amount_str.replace('$', '').replace(',', '')
    parts = [p.strip() for p in cleaned.split('-')]
    try:
        if len(parts) == 2:
            return {'low': float(parts[0]), 'high': float(parts[1])}
        return {'low': float(parts[0]), 'high': float(parts[0])}
    except ValueError:
        return {'low': 0.0, 'high': 0.0}


def get_congressional_trades(ticker: str, days_back: int = 365) -> Dict[str, Any]:
    """
    Fetch and filter Senate + House stock trading disclosures for a ticker.

    Returns individual transactions plus an aggregate buy/sell signal: net
    dollar-weighted direction over the lookback window, useful as a proxy for
    "smart money" / political sentiment on a stock.
    """
    ticker = _normalize_ticker(ticker)
    cutoff = datetime.now() - timedelta(days=days_back)

    try:
        senate_raw = _fetch_json(SENATE_URL, 'senate_stock_watcher_all')
        house_raw = _fetch_json(HOUSE_URL, 'house_stock_watcher_all')
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching congressional trading data: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Senate/House Stock Watcher',
        }

    transactions = []

    for row in senate_raw or []:
        row_ticker = _normalize_ticker(row.get('ticker', ''))
        if row_ticker != ticker:
            continue
        try:
            tx_date = datetime.strptime(row.get('transaction_date', ''), '%m/%d/%Y')
        except ValueError:
            continue
        if tx_date < cutoff:
            continue
        transactions.append({
            'chamber': 'Senate',
            'member': row.get('senator', 'Unknown'),
            'ticker': row_ticker,
            'transaction_type': row.get('type', 'Unknown'),
            'transaction_date': tx_date.isoformat(),
            'amount_range': row.get('amount', ''),
            'amount': _parse_amount_range(row.get('amount', '')),
            'asset_description': row.get('asset_description', ''),
        })

    for row in house_raw or []:
        row_ticker = _normalize_ticker(row.get('ticker', ''))
        if row_ticker != ticker:
            continue
        try:
            tx_date = datetime.strptime(row.get('transaction_date', ''), '%Y-%m-%d')
        except ValueError:
            continue
        if tx_date < cutoff:
            continue
        transactions.append({
            'chamber': 'House',
            'member': f"{row.get('representative', 'Unknown')}",
            'ticker': row_ticker,
            'transaction_type': row.get('type', 'Unknown'),
            'transaction_date': tx_date.isoformat(),
            'amount_range': row.get('amount', ''),
            'amount': _parse_amount_range(row.get('amount', '')),
            'asset_description': row.get('asset_description', ''),
        })

    transactions.sort(key=lambda t: t['transaction_date'], reverse=True)

    buy_dollars = 0.0
    sell_dollars = 0.0
    for tx in transactions:
        mid = (tx['amount']['low'] + tx['amount']['high']) / 2
        tx_type = tx['transaction_type'].lower()
        if 'purchase' in tx_type or tx_type == 'buy':
            buy_dollars += mid
        elif 'sale' in tx_type or 'sell' in tx_type:
            sell_dollars += mid

    total_dollars = buy_dollars + sell_dollars
    net_signal = 0.0 if total_dollars == 0 else (buy_dollars - sell_dollars) / total_dollars

    if not transactions:
        signal_label = 'no_activity'
    elif net_signal > 0.3:
        signal_label = 'net_buying'
    elif net_signal < -0.3:
        signal_label = 'net_selling'
    else:
        signal_label = 'mixed'

    return {
        'success': True,
        'ticker': ticker,
        'transactions': transactions[:50],
        'total_found': len(transactions),
        'lookback_days': days_back,
        'aggregate': {
            'buy_dollars_mid_estimate': round(buy_dollars, 2),
            'sell_dollars_mid_estimate': round(sell_dollars, 2),
            'net_signal': round(net_signal, 3),
            'signal_label': signal_label,
            'unique_members': len({t['member'] for t in transactions}),
        },
        'timestamp': datetime.now().isoformat(),
        'source': 'Senate/House Stock Watcher (STOCK Act disclosures)',
    }


if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"Testing congressional trading scraper for {test_ticker}...")
    result = get_congressional_trades(test_ticker)
    if result['success']:
        print(f"Found {result['total_found']} transactions, signal: {result['aggregate']['signal_label']}")
    else:
        print(f"Failed: {result['error']}")
