# analysis/sector_peers.py - Sector peer lookup
"""
yfinance doesn't expose a free, reliable "get peer companies" endpoint, so we
use a small curated list of large, liquid tickers per sector (matching the
sector names yfinance's `.info['sector']` returns for US equities). This is
deliberately static rather than dynamically scraped - it's predictable, has
no extra API dependency, and the sectors change composition slowly enough
that a curated list stays reasonably representative.

Used by both the valuation engine (comparable company multiples) and the
peer-performance logistic regression model (cross-sectional feature/label
data). Callers can always override with their own peer list.
"""

from typing import List, Optional
import yfinance as yf

SECTOR_PEERS = {
    'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'IBM', 'INTC', 'AMD', 'QCOM'],
    'Communication Services': ['GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'TMUS', 'VZ', 'T', 'CHTR', 'WBD'],
    'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'MAR'],
    'Consumer Defensive': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'PM', 'MDLZ', 'CL', 'KMB', 'GIS'],
    'Financial Services': ['JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'SCHW', 'BLK'],
    'Healthcare': ['UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'BMY'],
    'Industrials': ['CAT', 'GE', 'HON', 'UNP', 'BA', 'RTX', 'LMT', 'DE', 'UPS', 'MMM'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'WMB'],
    'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ED', 'PEG'],
    'Real Estate': ['PLD', 'AMT', 'EQIX', 'PSA', 'O', 'WELL', 'SPG', 'DLR', 'CCI', 'VICI'],
    'Basic Materials': ['LIN', 'SHW', 'APD', 'ECL', 'FCX', 'NEM', 'NUE', 'DOW', 'DD', 'PPG'],
}


def get_sector_peers(ticker: str, sector: Optional[str] = None, limit: int = 10) -> List[str]:
    """
    Return a list of peer tickers in the same sector as `ticker`, excluding
    the ticker itself. Pass `sector` directly to skip the yfinance lookup
    (e.g. when the caller already fetched .info elsewhere).
    """
    ticker = ticker.upper().strip()

    if sector is None:
        try:
            sector = yf.Ticker(ticker).info.get('sector')
        except Exception:
            sector = None

    peers = SECTOR_PEERS.get(sector, [])
    filtered = [p for p in peers if p != ticker]
    return filtered[:limit]


def get_all_sectors() -> List[str]:
    return list(SECTOR_PEERS.keys())
