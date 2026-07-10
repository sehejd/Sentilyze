# analysis/price_history.py - Lightweight price history for charting
"""
Real historical OHLCV + a couple of moving averages, formatted as plain JSON
records for the frontend's price chart. Separate from backtesting/engine.py
(which needs the full indicator set and simulates trades) - this just needs
to be fast and small for a dashboard sparkline/chart.
"""

from typing import Dict, Any
from datetime import datetime

from utils.yf_client import get_history
from backtesting.indicators import sma

PERIOD_MAP = {
    '1mo': '1mo', '3mo': '3mo', '6mo': '6mo', '1y': '1y', '2y': '2y', '5y': '5y',
}


def get_price_history(ticker: str, period: str = '6mo') -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    period = PERIOD_MAP.get(period, '6mo')

    try:
        df = get_history(ticker, period=period, auto_adjust=True)
    except Exception as e:
        return {'success': False, 'error': f"Error fetching price history for {ticker}: {str(e)}"}

    if df.empty:
        return {'success': False, 'error': f"No price history available for {ticker} (Yahoo Finance unavailable or rate limited)"}

    close = df['Close']
    sma_20 = sma(close, 20)
    sma_50 = sma(close, 50)

    points = []
    for i in range(len(df)):
        points.append({
            'date': str(df.index[i].date()),
            'close': round(float(close.iloc[i]), 2),
            'volume': int(df['Volume'].iloc[i]) if 'Volume' in df.columns and not df['Volume'].isna().iloc[i] else None,
            'sma_20': round(float(sma_20.iloc[i]), 2) if not sma_20.isna().iloc[i] else None,
            'sma_50': round(float(sma_50.iloc[i]), 2) if not sma_50.isna().iloc[i] else None,
        })

    first_close = float(close.iloc[0])
    last_close = float(close.iloc[-1])

    return {
        'success': True,
        'ticker': ticker,
        'period': period,
        'points': points,
        'period_return_pct': round((last_close / first_close - 1) * 100, 2),
        'period_high': round(float(df['High'].max()), 2) if 'High' in df.columns else None,
        'period_low': round(float(df['Low'].min()), 2) if 'Low' in df.columns else None,
        'timestamp': datetime.now().isoformat(),
        'source': 'Yahoo Finance (yfinance)',
    }
