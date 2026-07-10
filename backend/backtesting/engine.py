# backtesting/engine.py - Rule-based backtesting engine
"""
Simulates a simple long-only, fully-in-or-out strategy over real historical
daily price data (yfinance), driven by threshold rules on technical
indicators (see indicators.py) plus optional stop-loss/take-profit.

Honest limitation: point-in-time historical fundamentals (P/E, ROE, etc. as
they were *at each date in the past*) aren't available from free data
sources - yfinance and SEC EDGAR only expose current/as-currently-reported
figures. So "fundamental thresholds" in the backtest are applied as a single
static gate evaluated once against *today's* fundamentals (e.g. "only allow
this strategy to trade at all if current P/E < 25"), not as a per-day
historical filter. This is clearly labeled in the API response so it isn't
mistaken for point-in-time backtesting.
"""

from typing import Dict, List, Any, Optional
import math
import pandas as pd

from backtesting.indicators import compute_all_indicators
from utils.yf_client import get_history


def load_price_history(ticker: str, start: str, end: Optional[str] = None) -> pd.DataFrame:
    ticker = ticker.upper().strip()
    df = get_history(ticker, start=start, end=end, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No historical price data available for {ticker} in the given range")
    df.index = pd.to_datetime(df.index)
    return df


def _resolve_compare_value(df: pd.DataFrame, i: int, value: Any):
    if isinstance(value, str) and value in df.columns:
        return df[value].iloc[i]
    return value


def evaluate_rule(df: pd.DataFrame, i: int, rule: Dict[str, Any]) -> bool:
    field = rule.get('field')
    operator = rule.get('operator')
    value = rule.get('value')

    if field not in df.columns:
        return False

    current = df[field].iloc[i]
    if pd.isna(current):
        return False

    if operator in ('crosses_above', 'crosses_below'):
        if i == 0:
            return False
        prev = df[field].iloc[i - 1]
        curr_cmp = _resolve_compare_value(df, i, value)
        prev_cmp = _resolve_compare_value(df, i - 1, value)
        if any(v is None or (isinstance(v, float) and pd.isna(v)) for v in (prev, curr_cmp, prev_cmp)):
            return False
        if operator == 'crosses_above':
            return prev <= prev_cmp and current > curr_cmp
        return prev >= prev_cmp and current < curr_cmp

    compare_value = _resolve_compare_value(df, i, value)
    if compare_value is None or (isinstance(compare_value, float) and pd.isna(compare_value)):
        return False

    if operator == '<':
        return current < compare_value
    if operator == '<=':
        return current <= compare_value
    if operator == '>':
        return current > compare_value
    if operator == '>=':
        return current >= compare_value
    if operator == '==':
        return current == compare_value
    return False


def _max_drawdown(equity_series: List[float]) -> float:
    peak = -math.inf
    max_dd = 0.0
    for equity in equity_series:
        peak = max(peak, equity)
        if peak > 0:
            drawdown = (equity - peak) / peak
            max_dd = min(max_dd, drawdown)
    return round(max_dd * 100, 2)


def _sharpe_ratio(daily_returns: List[float]) -> Optional[float]:
    if len(daily_returns) < 2:
        return None
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return None
    return round((mean_return / std_dev) * math.sqrt(252), 3)


def run_backtest(
    ticker: str,
    start: str,
    end: Optional[str] = None,
    entry_rules: Optional[List[Dict[str, Any]]] = None,
    exit_rules: Optional[List[Dict[str, Any]]] = None,
    initial_capital: float = 10000.0,
    position_size_pct: float = 1.0,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
    entry_gate_passed: bool = True,
    entry_gate_note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the simulation. entry_rules are combined with AND to trigger a buy
    when flat; exit_rules are combined with OR to trigger a sell when in a
    position (in addition to stop_loss_pct / take_profit_pct if set).
    """
    entry_rules = entry_rules or []
    exit_rules = exit_rules or []
    position_size_pct = max(0.0, min(1.0, position_size_pct))

    raw = load_price_history(ticker, start, end)
    df = compute_all_indicators(raw)

    cash = initial_capital
    shares = 0.0
    in_position = False
    entry_price = None
    entry_date = None

    trades: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    first_valid_close = None
    last_valid_close = None
    first_valid_date = None
    last_valid_date = None

    for i in range(len(df)):
        close = df['close'].iloc[i]
        if pd.isna(close):
            continue

        date_str = str(df.index[i].date())
        if first_valid_close is None:
            first_valid_close = close
            first_valid_date = date_str
        last_valid_close = close
        last_valid_date = date_str

        if in_position:
            exit_triggered = False
            reason = None

            if stop_loss_pct and close <= entry_price * (1 - stop_loss_pct / 100):
                exit_triggered, reason = True, 'stop_loss'
            elif take_profit_pct and close >= entry_price * (1 + take_profit_pct / 100):
                exit_triggered, reason = True, 'take_profit'
            elif exit_rules and any(evaluate_rule(df, i, r) for r in exit_rules):
                exit_triggered, reason = True, 'exit_rule'

            if exit_triggered:
                proceeds = shares * close
                trade_return_pct = round((close / entry_price - 1) * 100, 2)
                trades.append({
                    'action': 'sell', 'date': date_str, 'price': round(close, 2),
                    'shares': round(shares, 4), 'proceeds': round(proceeds, 2),
                    'reason': reason, 'return_pct': trade_return_pct,
                    'entry_date': entry_date, 'entry_price': round(entry_price, 2),
                })
                cash += proceeds
                shares = 0.0
                in_position = False
                entry_price = None
                entry_date = None
        else:
            if entry_gate_passed and entry_rules and all(evaluate_rule(df, i, r) for r in entry_rules):
                invest_amount = cash * position_size_pct
                if invest_amount > 0:
                    bought_shares = invest_amount / close
                    shares = bought_shares
                    cash -= invest_amount
                    entry_price = close
                    entry_date = date_str
                    in_position = True
                    trades.append({
                        'action': 'buy', 'date': date_str, 'price': round(close, 2),
                        'shares': round(bought_shares, 4), 'cost': round(invest_amount, 2),
                    })

        equity = cash + shares * close
        equity_curve.append({'date': date_str, 'equity': round(equity, 2), 'close': round(close, 2)})

    if not equity_curve:
        raise ValueError("No valid trading days found to backtest in the given range")

    final_equity = equity_curve[-1]['equity']
    total_return_pct = round((final_equity / initial_capital - 1) * 100, 2)

    buy_hold_shares = initial_capital / first_valid_close
    buy_hold_equity_curve = [
        {'date': pt['date'], 'equity': round(buy_hold_shares * pt['close'], 2)}
        for pt in equity_curve
    ]
    buy_hold_return_pct = round((buy_hold_shares * last_valid_close / initial_capital - 1) * 100, 2)

    daily_returns = []
    for i in range(1, len(equity_curve)):
        prev_eq = equity_curve[i - 1]['equity']
        if prev_eq > 0:
            daily_returns.append((equity_curve[i]['equity'] - prev_eq) / prev_eq)

    completed_trades = [t for t in trades if t['action'] == 'sell']
    winning_trades = [t for t in completed_trades if t['return_pct'] > 0]
    win_rate_pct = round(len(winning_trades) / len(completed_trades) * 100, 1) if completed_trades else None

    days_elapsed = (pd.to_datetime(last_valid_date) - pd.to_datetime(first_valid_date)).days
    years_elapsed = max(days_elapsed / 365.25, 1 / 365.25)
    cagr_pct = round(((final_equity / initial_capital) ** (1 / years_elapsed) - 1) * 100, 2)

    return {
        'success': True,
        'ticker': ticker.upper().strip(),
        'period': {'start': first_valid_date, 'end': last_valid_date, 'requested_start': start, 'requested_end': end},
        'entry_gate': {'passed': entry_gate_passed, 'note': entry_gate_note},
        'initial_capital': initial_capital,
        'final_equity': round(final_equity, 2),
        'stats': {
            'total_return_pct': total_return_pct,
            'cagr_pct': cagr_pct,
            'max_drawdown_pct': _max_drawdown([pt['equity'] for pt in equity_curve]),
            'sharpe_ratio': _sharpe_ratio(daily_returns),
            'num_trades': len(completed_trades),
            'win_rate_pct': win_rate_pct,
            'buy_hold_return_pct': buy_hold_return_pct,
            'alpha_vs_buy_hold_pct': round(total_return_pct - buy_hold_return_pct, 2),
        },
        'trades': trades,
        'equity_curve': equity_curve,
        'buy_hold_equity_curve': buy_hold_equity_curve,
        'fundamental_gate_limitation': (
            "Fundamental thresholds (if any) are applied as a single static gate using "
            "current fundamentals, not a per-day historical filter - free data sources "
            "don't expose point-in-time historical fundamentals."
        ),
    }


if __name__ == "__main__":
    result = run_backtest(
        ticker="AAPL",
        start="2023-01-01",
        entry_rules=[{'field': 'rsi_14', 'operator': '<', 'value': 30}],
        exit_rules=[{'field': 'rsi_14', 'operator': '>', 'value': 70}],
    )
    print(result['stats'])
