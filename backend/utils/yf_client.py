# utils/yf_client.py - Centralized, cached, rate-limit-aware yfinance access
"""
Yahoo Finance's unofficial API (the one yfinance scrapes - there is no
official free API) aggressively rate-limits repeated requests, especially
from datacenter/cloud IPs. This has become a very common real-world failure
mode for yfinance-based apps (see e.g. ranaroussi/yfinance issues #2567,
#2568, #2518) and there is no complete fix on yfinance's side - impersonating
a browser session reduces but doesn't eliminate it.

Every feature in this app that touches company fundamentals goes through
`yf.Ticker(x).info` at some point (fundamentals, valuation, comps, sector
peers, company officers, backtesting's price history). Before this module
existed, none of those calls were cached, so a single dashboard load or a
peer-comparison run (10-20 tickers) fired that many fresh requests at Yahoo
in a few seconds - exactly the pattern that trips the rate limiter. If it
trips, *every* feature that depends on it degrades at once, which looks like
"the whole site is broken" even though the code itself is fine.

Fix: cache `.info` per ticker (fundamentals don't change minute to minute),
and retry with backoff on rate-limit-shaped errors before giving up. Route
every yfinance touchpoint through here instead of calling `yfinance` directly.
"""

import time
import random
import logging
from typing import Dict, Any, Callable, TypeVar, Optional

import yfinance as yf

from utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

T = TypeVar('T')

INFO_TTL_SECONDS = 15 * 60  # fundamentals/market snapshot data, not tick-by-tick
# A failed/empty fetch is cached only briefly - long enough to stop an
# immediate re-hammering of a hot rate-limit window, short enough that a
# transient blip self-heals in under two minutes instead of locking a ticker
# out for the full success TTL.
FAILURE_TTL_SECONDS = 90
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.5

try:
    from yfinance.exceptions import YFRateLimitError
except ImportError:  # older/newer yfinance without this exact class
    YFRateLimitError = None


class YFinanceUnavailable(Exception):
    """Raised when Yahoo Finance data couldn't be fetched after retries - almost
    always rate limiting. Callers should catch this and degrade gracefully
    (return success=False with a clear message) rather than crash."""
    pass


def _is_rate_limit_error(e: Exception) -> bool:
    if YFRateLimitError is not None and isinstance(e, YFRateLimitError):
        return True
    message = str(e).lower()
    return any(s in message for s in ('rate limit', '429', 'too many requests'))


def with_retry(fetch_fn: Callable[[], T], *, what: str = "yfinance request") -> T:
    """Run a yfinance call with exponential backoff + jitter on rate-limit errors."""
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            return fetch_fn()
        except Exception as e:
            last_error = e
            if not _is_rate_limit_error(e) or attempt == MAX_RETRIES - 1:
                break
            delay = BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 0.5)
            logger.warning(f"Yahoo Finance rate limited ({what}), retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)

    raise YFinanceUnavailable(
        f"Yahoo Finance data unavailable for {what} after {MAX_RETRIES} attempts "
        f"(likely rate limited): {last_error}"
    )


def get_info(ticker: str) -> Dict[str, Any]:
    """Cached, retrying fetch of yfinance's `.info` dict for a ticker.

    Successes are cached for INFO_TTL_SECONDS; failures/empty results only for
    the much shorter FAILURE_TTL_SECONDS, so a rate-limited ticker retries
    itself again on the next request after ~90s instead of staying "broken"
    for the full 15-minute success window.
    """
    ticker = ticker.upper().strip()
    cache_key = f"yf_info_{ticker}"

    recent = cache_get(cache_key, FAILURE_TTL_SECONDS)
    if recent is not None:
        return recent

    older = cache_get(cache_key, INFO_TTL_SECONDS)
    if older:
        return older

    try:
        data = with_retry(lambda: yf.Ticker(ticker).info, what=f".info for {ticker}")
    except YFinanceUnavailable:
        data = {}

    cache_set(cache_key, data)
    return data or {}


def get_history(ticker: str, **kwargs):
    """Retrying (not cached - callers pass varying date ranges) fetch of `.history()`."""
    ticker = ticker.upper().strip()
    return with_retry(lambda: yf.Ticker(ticker).history(**kwargs), what=f".history for {ticker}")


if __name__ == "__main__":
    info = get_info("AAPL")
    print(f"Fetched {len(info)} info fields for AAPL" if info else "No data (rate limited or network blocked)")
