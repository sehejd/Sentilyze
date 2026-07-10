# analysis/peer_performance_model.py - Cross-sectional logistic regression vs sector peers
"""
Compares a company's fundamentals, sentiment, and political (insider trading)
signal against its sector peers, and fits a logistic regression to identify
which of those indicators correlate with having outperformed the sector's
trailing price return.

Important methodological honesty: free data sources don't expose point-in-time
historical fundamentals (same limitation documented for the backtest engine),
so this is NOT a historical panel model trained across many past periods.
It's a **cross-sectional snapshot**: current fundamentals/sentiment/insider
data for ~10-15 sector peers, labeled by each peer's own trailing price
return relative to the sector median. The model is fit on peers only and
then scores the target company out-of-sample. With n typically in the
10-15 range, treat the coefficients as suggestive correlations within this
specific snapshot, not statistically robust findings - this is stated
explicitly in every response rather than left implicit.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from analysis.sector_peers import get_sector_peers
from analysis.fundamentals import get_fundamentals
from analysis.ml_sentiment import classify_batch
from scraping.yahoo import scrape_yahoo_stock
from scraping.insider_trading import get_congressional_trades
from utils.yf_client import get_info, get_history

FEATURE_NAMES = [
    'pe_ratio', 'price_to_book', 'debt_to_equity', 'return_on_equity',
    'profit_margin', 'revenue_growth', 'sentiment_compound', 'insider_signal',
]

FEATURE_LABELS = {
    'pe_ratio': 'P/E ratio', 'price_to_book': 'Price/Book', 'debt_to_equity': 'Debt/Equity',
    'return_on_equity': 'Return on equity', 'profit_margin': 'Profit margin',
    'revenue_growth': 'Revenue growth', 'sentiment_compound': 'News sentiment',
    'insider_signal': 'Congressional trading signal',
}


def _lightweight_sentiment(ticker: str) -> float:
    """Yahoo headlines only (not the full Reddit/Twitter fan-out) - keeps a ~15-peer batch fast."""
    try:
        data = scrape_yahoo_stock(ticker)
        if not data.get('success'):
            return 0.0
        texts = [f"{h.get('title', '')} {h.get('summary', '')}" for h in data.get('headlines', [])]
        return classify_batch(texts)['overall_compound']
    except Exception:
        return 0.0


def _insider_signal(ticker: str) -> float:
    try:
        result = get_congressional_trades(ticker, days_back=730)
        if result.get('success'):
            return result['aggregate']['net_signal']
    except Exception:
        pass
    return 0.0


def _trailing_return(ticker: str, months: int) -> Optional[float]:
    try:
        hist = get_history(ticker, period=f'{months}mo')
        if hist.empty or len(hist) < 2:
            return None
        return float(hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1)
    except Exception:
        return None


def _build_company_row(ticker: str, months: int) -> Optional[Dict[str, Any]]:
    fundamentals = get_fundamentals(ticker)
    if not fundamentals.get('success'):
        return None
    metrics = fundamentals['metrics']

    row = {
        'ticker': ticker,
        'pe_ratio': metrics.get('pe_ratio'),
        'price_to_book': metrics.get('price_to_book'),
        'debt_to_equity': metrics.get('debt_to_equity'),
        'return_on_equity': metrics.get('return_on_equity'),
        'profit_margin': metrics.get('profit_margin'),
        'revenue_growth': metrics.get('revenue_growth'),
        'sentiment_compound': _lightweight_sentiment(ticker),
        'insider_signal': _insider_signal(ticker),
        'trailing_return': _trailing_return(ticker, months),
        'company_name': fundamentals.get('company_name', ticker),
    }
    return row


def _impute_and_scale(rows: List[Dict[str, Any]]) -> np.ndarray:
    """Median-impute missing feature values per column, then z-score standardize."""
    matrix = np.array([[r.get(f) for f in FEATURE_NAMES] for r in rows], dtype=float)
    for col in range(matrix.shape[1]):
        column = matrix[:, col]
        valid = column[~np.isnan(column)]
        median = np.median(valid) if len(valid) > 0 else 0.0
        column[np.isnan(column)] = median
        matrix[:, col] = column

    scaler = StandardScaler()
    return scaler.fit_transform(matrix)


def run_peer_performance_analysis(
    ticker: str,
    lookback_months: int = 12,
    peer_tickers: Optional[List[str]] = None,
    min_peers: int = 6,
) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    target_info = get_info(ticker)
    if not target_info:
        return {'success': False, 'error': f"No data found for {ticker} (Yahoo Finance unavailable or rate limited)"}

    sector = target_info.get('sector')
    peers = peer_tickers or get_sector_peers(ticker, sector=sector, limit=15)

    if len(peers) < min_peers:
        return {
            'success': False,
            'error': f"Not enough sector peers found for '{sector}' (need at least {min_peers}, got {len(peers)}).",
        }

    all_tickers = peers + [ticker]
    with ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(lambda t: _build_company_row(t, lookback_months), all_tickers))

    rows_by_ticker = {r['ticker']: r for r in rows if r is not None}
    target_row = rows_by_ticker.pop(ticker, None)
    peer_rows = [r for r in rows_by_ticker.values() if r.get('trailing_return') is not None]

    if target_row is None:
        return {'success': False, 'error': f"Could not compute fundamentals for {ticker} itself."}
    if len(peer_rows) < min_peers:
        return {
            'success': False,
            'error': f"Only {len(peer_rows)} of {len(peers)} peers had usable data (need at least {min_peers}). Try a larger peer list.",
        }

    peer_returns = [r['trailing_return'] for r in peer_rows]
    median_return = statistics.median(peer_returns)
    for r in peer_rows:
        r['outperformed'] = 1 if r['trailing_return'] > median_return else 0

    labels = [r['outperformed'] for r in peer_rows]
    if len(set(labels)) < 2:
        return {
            'success': False,
            'error': 'All sector peers landed on the same side of the median return (degenerate split) - cannot fit a classifier on a single class.',
        }

    X_peers = _impute_and_scale(peer_rows)
    y_peers = np.array(labels)

    # Refit the scaler jointly over peers+target so the target's features are
    # transformed consistently, then split back apart for fit vs score.
    combined_rows = peer_rows + [target_row]
    X_combined = _impute_and_scale(combined_rows)
    X_peers_scaled = X_combined[:-1]
    X_target_scaled = X_combined[-1:].reshape(1, -1)

    model = LogisticRegression(max_iter=1000, C=0.5)
    model.fit(X_peers_scaled, y_peers)

    target_probability = float(model.predict_proba(X_target_scaled)[0][1])
    target_return = target_row.get('trailing_return')
    target_outperformed = (target_return > median_return) if target_return is not None else None

    coefficients = sorted(
        [
            {
                'feature': f,
                'label': FEATURE_LABELS[f],
                'coefficient': round(float(coef), 4),
                'direction': 'positively correlated with outperformance' if coef > 0 else 'negatively correlated with outperformance',
            }
            for f, coef in zip(FEATURE_NAMES, model.coef_[0])
        ],
        key=lambda c: abs(c['coefficient']),
        reverse=True,
    )

    peer_table = sorted(
        [
            {
                'ticker': r['ticker'], 'company_name': r.get('company_name', r['ticker']),
                'trailing_return_pct': round(r['trailing_return'] * 100, 1),
                'outperformed_median': bool(r['outperformed']),
            }
            for r in peer_rows
        ],
        key=lambda r: r['trailing_return_pct'], reverse=True,
    )

    return {
        'success': True,
        'ticker': ticker,
        'sector': sector,
        'lookback_months': lookback_months,
        'peer_count': len(peer_rows),
        'sector_median_return_pct': round(median_return * 100, 1),
        'target': {
            'trailing_return_pct': round(target_return * 100, 1) if target_return is not None else None,
            'outperformed_median': target_outperformed,
            'predicted_probability_of_outperformance': round(target_probability, 3),
            'features': {f: target_row.get(f) for f in FEATURE_NAMES},
        },
        'model': {
            'type': 'logistic_regression',
            'trained_on': 'sector peers only (target scored out-of-sample)',
            'regularization_C': 0.5,
            'coefficients': coefficients,
            'train_accuracy': round(float(model.score(X_peers_scaled, y_peers)), 3),
        },
        'peer_table': peer_table,
        'timestamp': datetime.now().isoformat(),
        'methodology_caveat': (
            f"This is a cross-sectional snapshot of {len(peer_rows)} current sector peers, not a "
            "historical panel - free data sources don't expose point-in-time historical fundamentals "
            "(same limitation as the backtest engine's fundamental gate). With this few observations, "
            "treat the coefficients as suggestive correlations within this specific peer snapshot at "
            "this point in time, not statistically robust or forward-predictive findings."
        ),
    }


if __name__ == "__main__":
    result = run_peer_performance_analysis("AAPL")
    if result.get('success'):
        print(f"Target outperformance probability: {result['target']['predicted_probability_of_outperformance']}")
        for c in result['model']['coefficients'][:3]:
            print(f"  {c['label']}: {c['coefficient']} ({c['direction']})")
    else:
        print(result.get('error'))
