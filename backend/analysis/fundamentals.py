# analysis/fundamentals.py - Fundamental analysis & scoring engine
"""
Builds a fundamental picture of a company by combining:

- yfinance `.info` for market-priced ratios (P/E, PEG, price/book, margins,
  growth rates, dividend yield, beta) - fast, always available for listed
  tickers.
- SEC EDGAR XBRL company facts (scraping/sec_edgar.py) for as-reported
  figures straight from 10-Q/10-K filings, used as a cross-check and for
  metrics yfinance doesn't expose directly (e.g. quarter-over-quarter
  revenue growth computed from raw filed numbers).

Each metric is scored 0-100 against configurable threshold bands and rolled
into a single weighted fundamental score. The same threshold bands are
reused by the backtesting engine so "buy when P/E < 20" means the same thing
in both places.
"""

from typing import Dict, Any, Optional
import math
import yfinance as yf

from scraping.sec_edgar import get_company_facts

# Default threshold bands per metric: (excellent_cutoff, good_cutoff, fair_cutoff)
# direction='low' means lower values are better (crosses bands descending),
# direction='high' means higher values are better (crosses bands ascending).
DEFAULT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    'pe_ratio':          {'direction': 'low',  'bands': (15, 25, 35), 'weight': 0.15},
    'peg_ratio':         {'direction': 'low',  'bands': (1.0, 1.5, 2.5), 'weight': 0.10},
    'price_to_book':     {'direction': 'low',  'bands': (1.5, 3.0, 5.0), 'weight': 0.05},
    'debt_to_equity':    {'direction': 'low',  'bands': (0.5, 1.0, 2.0), 'weight': 0.15},
    'current_ratio':     {'direction': 'high', 'bands': (2.0, 1.5, 1.0), 'weight': 0.10},
    'return_on_equity':  {'direction': 'high', 'bands': (0.20, 0.12, 0.05), 'weight': 0.15},
    'profit_margin':     {'direction': 'high', 'bands': (0.20, 0.10, 0.03), 'weight': 0.10},
    'revenue_growth':    {'direction': 'high', 'bands': (0.15, 0.05, 0.0), 'weight': 0.10},
    'earnings_growth':   {'direction': 'high', 'bands': (0.15, 0.05, 0.0), 'weight': 0.10},
}


def _score_metric(value: Optional[float], direction: str, bands: tuple) -> Optional[float]:
    """Score a single metric 0-100 against its threshold bands. None if value missing."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None

    excellent, good, fair = bands
    if direction == 'low':
        if value <= excellent:
            return 100.0
        if value <= good:
            return 75.0
        if value <= fair:
            return 50.0
        return 25.0
    else:  # 'high'
        if value >= excellent:
            return 100.0
        if value >= good:
            return 75.0
        if value >= fair:
            return 50.0
        return 25.0


def get_fundamentals(ticker: str) -> Dict[str, Any]:
    """Pull market ratios (yfinance) + as-reported figures (SEC EDGAR) for a ticker."""
    ticker = ticker.upper().strip()

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        return {'success': False, 'error': f"Error fetching yfinance data for {ticker}: {str(e)}"}

    if not info or info.get('trailingPE') is None and info.get('regularMarketPrice') is None:
        return {'success': False, 'error': f"No fundamental data available for {ticker}"}

    metrics = {
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': info.get('pegRatio') or info.get('trailingPegRatio'),
        'price_to_book': info.get('priceToBook'),
        'debt_to_equity': (info.get('debtToEquity') / 100.0) if info.get('debtToEquity') else None,
        'current_ratio': info.get('currentRatio'),
        'quick_ratio': info.get('quickRatio'),
        'return_on_equity': info.get('returnOnEquity'),
        'return_on_assets': info.get('returnOnAssets'),
        'profit_margin': info.get('profitMargins'),
        'operating_margin': info.get('operatingMargins'),
        'gross_margin': info.get('grossMargins'),
        'revenue_growth': info.get('revenueGrowth'),
        'earnings_growth': info.get('earningsGrowth'),
        'dividend_yield': info.get('dividendYield'),
        'beta': info.get('beta'),
        'market_cap': info.get('marketCap'),
        'free_cash_flow': info.get('freeCashflow'),
        'total_cash': info.get('totalCash'),
        'total_debt': info.get('totalDebt'),
    }

    sec_facts = get_company_facts(ticker)
    sec_summary = None
    if sec_facts.get('success'):
        sec_metrics = sec_facts.get('metrics', {})
        sec_summary = {
            name: {
                'latest_value': m.get('latest_value'),
                'latest_period_end': m.get('latest_period_end'),
                'latest_form': m.get('latest_form'),
            }
            for name, m in sec_metrics.items()
        }

    return {
        'success': True,
        'ticker': ticker,
        'company_name': info.get('longName', ticker),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'metrics': metrics,
        'as_reported_sec_data': sec_summary,
        'source': 'yfinance + SEC EDGAR XBRL',
    }


def score_fundamentals(metrics: Dict[str, Any], thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Score a metrics dict (as returned by get_fundamentals()['metrics']) 0-100."""
    thresholds = thresholds or DEFAULT_THRESHOLDS

    breakdown = []
    weighted_sum = 0.0
    weight_total = 0.0

    for metric_name, config in thresholds.items():
        value = metrics.get(metric_name)
        score = _score_metric(value, config['direction'], config['bands'])
        breakdown.append({
            'metric': metric_name,
            'value': value,
            'score': score,
            'weight': config['weight'],
        })
        if score is not None:
            weighted_sum += score * config['weight']
            weight_total += config['weight']

    overall_score = round(weighted_sum / weight_total, 1) if weight_total > 0 else None

    if overall_score is None:
        rating = 'insufficient_data'
    elif overall_score >= 85:
        rating = 'strong'
    elif overall_score >= 65:
        rating = 'good'
    elif overall_score >= 45:
        rating = 'fair'
    else:
        rating = 'weak'

    return {
        'overall_score': overall_score,
        'rating': rating,
        'breakdown': breakdown,
        'data_coverage': f"{sum(1 for b in breakdown if b['score'] is not None)}/{len(breakdown)}",
    }


def evaluate_metric_checks(metrics: Dict[str, Any], checks: list) -> Dict[str, Any]:
    """
    Evaluate a list of static threshold checks against current fundamentals,
    e.g. [{"metric": "pe_ratio", "operator": "<", "value": 25}]. Used as the
    backtest engine's one-time "fundamental gate" (see backtesting/engine.py
    for why this can't be a per-day historical filter).
    """
    ops = {
        '<': lambda a, b: a < b, '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b, '>=': lambda a, b: a >= b,
        '==': lambda a, b: a == b,
    }

    details = []
    all_passed = True
    for check in checks:
        metric_name = check.get('metric')
        operator = check.get('operator')
        threshold_value = check.get('value')
        actual_value = metrics.get(metric_name)

        if actual_value is None or operator not in ops:
            details.append({**check, 'actual_value': actual_value, 'passed': False, 'note': 'metric unavailable'})
            all_passed = False
            continue

        passed = ops[operator](actual_value, threshold_value)
        details.append({**check, 'actual_value': actual_value, 'passed': passed})
        if not passed:
            all_passed = False

    return {'passed': all_passed, 'checks': details}


def get_fundamental_analysis(ticker: str, thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience wrapper: fetch + score in one call."""
    fundamentals = get_fundamentals(ticker)
    if not fundamentals.get('success'):
        return fundamentals

    scoring = score_fundamentals(fundamentals['metrics'], thresholds)
    fundamentals['scoring'] = scoring
    return fundamentals


if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"Testing fundamentals engine for {test_ticker}...")
    result = get_fundamental_analysis(test_ticker)
    if result.get('success'):
        print(f"Score: {result['scoring']['overall_score']} ({result['scoring']['rating']})")
    else:
        print(f"Failed: {result.get('error')}")
