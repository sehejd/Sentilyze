# backtesting/indicators.py - Technical indicator calculations
"""
Standard technical indicators computed on a pandas OHLCV DataFrame (as
returned by yfinance's `.history()`). Kept dependency-free beyond
pandas/numpy so the backtest engine doesn't need TA-Lib or similar.
"""

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, window: int) -> pd.Series:
    return close.ewm(span=window, adjust=False, min_periods=window).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    result = 100 - (100 / (1 + rs))
    return result.fillna(50.0)  # neutral where undefined (e.g. no losses at all)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(close, window)
    std = close.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def volume_avg(volume: pd.Series, window: int = 20) -> pd.Series:
    return volume.rolling(window=window, min_periods=window).mean()


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Attach every supported indicator as columns to a copy of the OHLCV frame."""
    out = df.copy()
    close = out['Close']

    out['sma_20'] = sma(close, 20)
    out['sma_50'] = sma(close, 50)
    out['sma_200'] = sma(close, 200)
    out['ema_12'] = ema(close, 12)
    out['ema_26'] = ema(close, 26)
    out['rsi_14'] = rsi(close, 14)

    macd_line, signal_line, hist = macd(close)
    out['macd'] = macd_line
    out['macd_signal'] = signal_line
    out['macd_histogram'] = hist

    upper, mid, lower = bollinger_bands(close)
    out['bb_upper'] = upper
    out['bb_mid'] = mid
    out['bb_lower'] = lower

    if 'Volume' in out.columns:
        out['volume_avg_20'] = volume_avg(out['Volume'], 20)
        out['volume'] = out['Volume']

    out['pct_change'] = close.pct_change() * 100
    out['close'] = close

    return out


# Fields available for the backtest rule builder, with metadata for the frontend
AVAILABLE_INDICATORS = {
    'close': {'label': 'Close price', 'unit': '$'},
    'sma_20': {'label': '20-day SMA', 'unit': '$'},
    'sma_50': {'label': '50-day SMA', 'unit': '$'},
    'sma_200': {'label': '200-day SMA', 'unit': '$'},
    'ema_12': {'label': '12-day EMA', 'unit': '$'},
    'ema_26': {'label': '26-day EMA', 'unit': '$'},
    'rsi_14': {'label': 'RSI (14)', 'unit': '', 'range': [0, 100]},
    'macd': {'label': 'MACD line', 'unit': ''},
    'macd_signal': {'label': 'MACD signal line', 'unit': ''},
    'macd_histogram': {'label': 'MACD histogram', 'unit': ''},
    'bb_upper': {'label': 'Bollinger upper band', 'unit': '$'},
    'bb_lower': {'label': 'Bollinger lower band', 'unit': '$'},
    'volume_avg_20': {'label': '20-day avg volume', 'unit': ''},
    'volume': {'label': 'Volume', 'unit': ''},
    'pct_change': {'label': 'Daily % change', 'unit': '%'},
}

OPERATORS = ['<', '<=', '>', '>=', '==', 'crosses_above', 'crosses_below']
