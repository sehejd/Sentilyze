# analysis/valuation.py - Multi-method fundamental valuation calculator
"""
Estimates intrinsic/fair value per share using five standard fundamental
valuation methodologies, each independently computed and clearly labeled
with its own assumptions (valuation is assumption-driven by nature - hiding
that would be misleading):

  1. Discounted Cash Flow (DCF)       - project FCF, discount at WACC, add terminal value
  2. Comparable Company Analysis      - apply sector-peer median multiples (P/E, EV/EBITDA, P/S)
  3. Dividend Discount Model (DDM)    - Gordon Growth Model, dividend payers only
  4. Graham Number                    - Benjamin Graham's classic formula
  5. Asset-based (Book Value)         - net asset value per share, a conservative floor

None of this is investment advice - every method is sensitive to its inputs,
and reasonable analysts disagree on assumptions like growth rates and
discount rates. The point is to show several independent lenses on the same
company, not to produce a single "correct" number.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import math

from analysis.sector_peers import get_sector_peers
from utils.yf_client import get_info, get_history

EQUITY_RISK_PREMIUM = 0.05  # Damodaran-style long-run US ERP estimate
DEFAULT_RISK_FREE_RATE = 0.045
DEFAULT_COST_OF_DEBT = 0.05
DEFAULT_TAX_RATE = 0.21
TERMINAL_GROWTH_RATE = 0.025  # ~long-run nominal GDP growth assumption
PROJECTION_YEARS = 5


def _get_risk_free_rate() -> float:
    """10-year US Treasury yield (^TNX quotes it as e.g. 45.0 meaning 4.50%)."""
    try:
        hist = get_history('^TNX', period='5d')
        if not hist.empty:
            return float(hist['Close'].iloc[-1]) / 1000  # ^TNX is quoted *10 in percentage points
    except Exception:
        pass
    return DEFAULT_RISK_FREE_RATE


def _estimate_wacc(info: Dict[str, Any], financials: Optional[Any] = None) -> Dict[str, Any]:
    risk_free_rate = _get_risk_free_rate()
    beta = info.get('beta') or 1.0
    cost_of_equity = risk_free_rate + beta * EQUITY_RISK_PREMIUM

    tax_rate = DEFAULT_TAX_RATE
    cost_of_debt = DEFAULT_COST_OF_DEBT

    market_cap = info.get('marketCap') or 0
    total_debt = info.get('totalDebt') or 0

    total_capital = market_cap + total_debt
    if total_capital > 0:
        equity_weight = market_cap / total_capital
        debt_weight = total_debt / total_capital
    else:
        equity_weight, debt_weight = 1.0, 0.0

    after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
    wacc = equity_weight * cost_of_equity + debt_weight * after_tax_cost_of_debt
    wacc = max(0.04, min(0.20, wacc))  # guard against degenerate inputs producing nonsense discount rates

    return {
        'wacc': round(wacc, 4),
        'risk_free_rate': round(risk_free_rate, 4),
        'beta': round(beta, 3),
        'cost_of_equity': round(cost_of_equity, 4),
        'cost_of_debt': round(cost_of_debt, 4),
        'tax_rate': tax_rate,
        'equity_weight': round(equity_weight, 3),
        'debt_weight': round(debt_weight, 3),
    }


def discounted_cash_flow(ticker: str, info: Dict[str, Any]) -> Dict[str, Any]:
    """Project free cash flow forward, discount at WACC, add a terminal value."""
    fcf = info.get('freeCashflow')
    shares_outstanding = info.get('sharesOutstanding')
    total_debt = info.get('totalDebt') or 0
    total_cash = info.get('totalCash') or 0
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

    if not fcf or fcf <= 0 or not shares_outstanding:
        return {
            'method': 'dcf', 'applicable': False,
            'note': 'No positive free cash flow data available - DCF requires positive FCF to project.',
        }

    wacc_data = _estimate_wacc(info)
    wacc = wacc_data['wacc']

    growth_rate = info.get('revenueGrowth') or info.get('earningsGrowth') or 0.05
    growth_rate = max(-0.10, min(0.25, growth_rate))  # clip to plausible near-term bounds

    if wacc <= TERMINAL_GROWTH_RATE:
        return {'method': 'dcf', 'applicable': False, 'note': 'WACC estimate too close to terminal growth rate for a meaningful terminal value.'}

    projected_fcf = []
    fcf_year = fcf
    for year in range(1, PROJECTION_YEARS + 1):
        # linearly decay growth toward the terminal rate over the projection window
        year_growth = growth_rate + (TERMINAL_GROWTH_RATE - growth_rate) * (year / PROJECTION_YEARS)
        fcf_year = fcf_year * (1 + year_growth)
        projected_fcf.append(fcf_year)

    discounted_fcf = [cf / ((1 + wacc) ** year) for year, cf in enumerate(projected_fcf, start=1)]
    terminal_value = projected_fcf[-1] * (1 + TERMINAL_GROWTH_RATE) / (wacc - TERMINAL_GROWTH_RATE)
    discounted_terminal_value = terminal_value / ((1 + wacc) ** PROJECTION_YEARS)

    enterprise_value = sum(discounted_fcf) + discounted_terminal_value
    equity_value = enterprise_value - total_debt + total_cash
    fair_value_per_share = equity_value / shares_outstanding

    return {
        'method': 'dcf',
        'applicable': True,
        'fair_value_per_share': round(fair_value_per_share, 2),
        'current_price': current_price,
        'upside_pct': round((fair_value_per_share / current_price - 1) * 100, 1) if current_price else None,
        'assumptions': {
            **wacc_data,
            'starting_fcf': fcf,
            'initial_growth_rate': round(growth_rate, 4),
            'terminal_growth_rate': TERMINAL_GROWTH_RATE,
            'projection_years': PROJECTION_YEARS,
        },
        'note': 'Highly sensitive to growth and discount rate assumptions above - treat as one scenario, not a precise target.',
    }


def _fetch_peer_multiples(peer_ticker: str) -> Optional[Dict[str, Any]]:
    try:
        info = get_info(peer_ticker)
        if not info:
            return None
        market_cap = info.get('marketCap')
        ebitda = info.get('ebitda')
        total_debt = info.get('totalDebt') or 0
        total_cash = info.get('totalCash') or 0
        ev = (market_cap + total_debt - total_cash) if market_cap else None

        return {
            'ticker': peer_ticker,
            'pe_ratio': info.get('trailingPE'),
            'ev_to_ebitda': (ev / ebitda) if ev and ebitda and ebitda > 0 else None,
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
        }
    except Exception:
        return None


def comparable_company_analysis(ticker: str, info: Dict[str, Any], peer_tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Apply sector-peer median multiples to the company's own EPS/EBITDA/revenue per share."""
    peer_tickers = peer_tickers or get_sector_peers(ticker, sector=info.get('sector'))
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

    if not peer_tickers:
        return {'method': 'comparable_company_analysis', 'applicable': False, 'note': f"No peer list available for sector '{info.get('sector')}'."}

    with ThreadPoolExecutor(max_workers=6) as executor:
        peer_data = [r for r in executor.map(_fetch_peer_multiples, peer_tickers) if r]

    def median(values: List[float]) -> Optional[float]:
        clean = sorted(v for v in values if v is not None and v > 0)
        if not clean:
            return None
        mid = len(clean) // 2
        return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2

    median_pe = median([p['pe_ratio'] for p in peer_data])
    median_ev_ebitda = median([p['ev_to_ebitda'] for p in peer_data])
    median_ps = median([p['price_to_sales'] for p in peer_data])

    eps = info.get('trailingEps')
    revenue_per_share = info.get('revenuePerShare')
    ebitda = info.get('ebitda')
    shares_outstanding = info.get('sharesOutstanding')
    total_debt = info.get('totalDebt') or 0
    total_cash = info.get('totalCash') or 0

    implied_values = {}
    if median_pe and eps and eps > 0:
        implied_values['pe_implied'] = round(median_pe * eps, 2)
    if median_ps and revenue_per_share and revenue_per_share > 0:
        implied_values['ps_implied'] = round(median_ps * revenue_per_share, 2)
    if median_ev_ebitda and ebitda and ebitda > 0 and shares_outstanding:
        implied_ev = median_ev_ebitda * ebitda
        implied_equity = implied_ev - total_debt + total_cash
        implied_values['ev_ebitda_implied'] = round(implied_equity / shares_outstanding, 2)

    if not implied_values:
        return {
            'method': 'comparable_company_analysis', 'applicable': False,
            'note': 'Insufficient peer or company multiple data to derive an implied value.',
            'peers_used': [p['ticker'] for p in peer_data],
        }

    fair_value_per_share = round(sum(implied_values.values()) / len(implied_values), 2)

    return {
        'method': 'comparable_company_analysis',
        'applicable': True,
        'fair_value_per_share': fair_value_per_share,
        'current_price': current_price,
        'upside_pct': round((fair_value_per_share / current_price - 1) * 100, 1) if current_price else None,
        'assumptions': {
            'peers_used': [p['ticker'] for p in peer_data],
            'median_pe': round(median_pe, 2) if median_pe else None,
            'median_ev_to_ebitda': round(median_ev_ebitda, 2) if median_ev_ebitda else None,
            'median_price_to_sales': round(median_ps, 2) if median_ps else None,
            'implied_values_by_multiple': implied_values,
        },
        'note': 'Average of implied values from peer median P/E, EV/EBITDA, and P/S multiples (only multiples with sufficient data are used).',
    }


def dividend_discount_model(info: Dict[str, Any]) -> Dict[str, Any]:
    """Gordon Growth Model - only meaningful for stable dividend payers."""
    dividend_rate = info.get('dividendRate')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

    if not dividend_rate or dividend_rate <= 0:
        return {'method': 'ddm', 'applicable': False, 'note': 'Company does not pay a dividend - DDM is not meaningful.'}

    wacc_data = _estimate_wacc(info)
    cost_of_equity = wacc_data['cost_of_equity']

    # Conservative dividend growth estimate: half of earnings growth (payout tends to grow slower
    # than earnings), floored at 0 and capped well below cost of equity to keep the formula sane.
    earnings_growth = info.get('earningsGrowth') or 0.04
    dividend_growth_rate = max(0.0, min(cost_of_equity - 0.02, earnings_growth / 2))

    if cost_of_equity <= dividend_growth_rate:
        return {'method': 'ddm', 'applicable': False, 'note': 'Cost of equity estimate too close to assumed dividend growth rate.'}

    next_year_dividend = dividend_rate * (1 + dividend_growth_rate)
    fair_value_per_share = next_year_dividend / (cost_of_equity - dividend_growth_rate)

    return {
        'method': 'ddm',
        'applicable': True,
        'fair_value_per_share': round(fair_value_per_share, 2),
        'current_price': current_price,
        'upside_pct': round((fair_value_per_share / current_price - 1) * 100, 1) if current_price else None,
        'assumptions': {
            'current_dividend_rate': dividend_rate,
            'dividend_growth_rate': round(dividend_growth_rate, 4),
            'cost_of_equity': cost_of_equity,
        },
        'note': 'Gordon Growth Model - assumes a constant dividend growth rate forever, which rarely holds exactly.',
    }


def graham_number(info: Dict[str, Any]) -> Dict[str, Any]:
    """Benjamin Graham's classic conservative intrinsic value formula: sqrt(22.5 * EPS * BVPS)."""
    eps = info.get('trailingEps')
    book_value_per_share = info.get('bookValue')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

    if not eps or eps <= 0 or not book_value_per_share or book_value_per_share <= 0:
        return {'method': 'graham_number', 'applicable': False, 'note': 'Requires positive EPS and positive book value per share.'}

    fair_value_per_share = round(math.sqrt(22.5 * eps * book_value_per_share), 2)

    return {
        'method': 'graham_number',
        'applicable': True,
        'fair_value_per_share': fair_value_per_share,
        'current_price': current_price,
        'upside_pct': round((fair_value_per_share / current_price - 1) * 100, 1) if current_price else None,
        'assumptions': {'eps': eps, 'book_value_per_share': book_value_per_share},
        'note': "Benjamin Graham's original formula, designed for conservative value investing in stable industrial companies - tends to undervalue high-growth or asset-light businesses.",
    }


def asset_based_valuation(info: Dict[str, Any]) -> Dict[str, Any]:
    """Net asset value per share - a conservative floor, most meaningful for asset-heavy or financial companies."""
    book_value_per_share = info.get('bookValue')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

    if not book_value_per_share or book_value_per_share <= 0:
        return {'method': 'asset_based', 'applicable': False, 'note': 'No positive book value per share available.'}

    return {
        'method': 'asset_based',
        'applicable': True,
        'fair_value_per_share': round(book_value_per_share, 2),
        'current_price': current_price,
        'upside_pct': round((book_value_per_share / current_price - 1) * 100, 1) if current_price else None,
        'assumptions': {'book_value_per_share': book_value_per_share},
        'note': 'Net asset value (book value) per share - a conservative floor estimate, most relevant for asset-heavy or financial companies and least relevant for asset-light/high-growth businesses.',
    }


def run_valuation(ticker: str, peer_tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run every applicable valuation method and blend the results."""
    ticker = ticker.upper().strip()

    info = get_info(ticker)

    if not info or (info.get('currentPrice') is None and info.get('regularMarketPrice') is None):
        return {'success': False, 'error': f"No market data available for {ticker} (Yahoo Finance unavailable or rate limited)"}

    methods = [
        discounted_cash_flow(ticker, info),
        comparable_company_analysis(ticker, info, peer_tickers),
        dividend_discount_model(info),
        graham_number(info),
        asset_based_valuation(info),
    ]

    applicable = [m for m in methods if m.get('applicable')]
    blended_fair_value = None
    rating = 'insufficient_data'

    if applicable:
        blended_fair_value = round(sum(m['fair_value_per_share'] for m in applicable) / len(applicable), 2)
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        blended_upside_pct = round((blended_fair_value / current_price - 1) * 100, 1) if current_price else None

        if blended_upside_pct is not None:
            if blended_upside_pct >= 15:
                rating = 'undervalued'
            elif blended_upside_pct <= -15:
                rating = 'overvalued'
            else:
                rating = 'fairly_valued'
    else:
        blended_upside_pct = None

    return {
        'success': True,
        'ticker': ticker,
        'company_name': info.get('longName', ticker),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
        'methods': methods,
        'methods_applicable': len(applicable),
        'blended_fair_value_per_share': blended_fair_value,
        'blended_upside_pct': blended_upside_pct,
        'rating': rating,
        'timestamp': datetime.now().isoformat(),
        'disclaimer': (
            "Each method uses different, independently-stated assumptions (growth rates, discount "
            "rates, peer multiples). The blended figure is a simple average across applicable methods, "
            "not a statistically weighted 'best estimate' - review the individual methods and their "
            "assumptions rather than relying on the blended number alone. Not investment advice."
        ),
    }


if __name__ == "__main__":
    result = run_valuation("AAPL")
    if result.get('success'):
        print(f"Blended fair value: {result['blended_fair_value_per_share']} ({result['rating']})")
        for m in result['methods']:
            print(f"  {m['method']}: applicable={m['applicable']}", m.get('fair_value_per_share'))
    else:
        print(result.get('error'))
