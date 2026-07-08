# scraping/social_trends.py - Social-media-driven momentum & trend scraper
"""
Measures how fast chatter about a ticker is accelerating, which is often a
leading indicator for retail-driven ("meme stock") moves independent of
fundamentals:

1. Reddit mention velocity: today's mention rate across finance subreddits vs
   the trailing week's daily average, using Reddit's public search JSON API
   (same endpoint as scraping/reddit.py, no auth required).
2. Google Trends search interest via pytrends (optional dependency - the app
   degrades gracefully if it isn't installed or Google rate-limits us).
"""

import requests
from typing import Dict, Any
from datetime import datetime
import time

SUBREDDITS = ['stocks', 'investing', 'wallstreetbets', 'StockMarket']
_HEADERS = {'User-Agent': 'SentilyzeBot/1.0 (Stock Analysis Tool)'}


def _count_mentions(ticker: str, timeframe: str) -> int:
    total = 0
    for subreddit in SUBREDDITS:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{subreddit}/search.json",
                params={'q': f"${ticker} OR {ticker}", 'sort': 'new', 'limit': 100,
                        'restrict_sr': 'on', 't': timeframe},
                headers=_HEADERS, timeout=10,
            )
            if resp.status_code == 200:
                total += len(resp.json().get('data', {}).get('children', []))
            time.sleep(0.3)
        except requests.RequestException:
            continue
    return total


def get_reddit_momentum(ticker: str) -> Dict[str, Any]:
    """Compare today's Reddit mention volume to the trailing week's daily average."""
    ticker = ticker.upper().strip()
    try:
        today_count = _count_mentions(ticker, 'day')
        week_count = _count_mentions(ticker, 'week')
        week_daily_avg = week_count / 7.0

        if week_daily_avg == 0:
            velocity_ratio = 1.0 if today_count == 0 else float(today_count)
        else:
            velocity_ratio = today_count / week_daily_avg

        if velocity_ratio >= 3:
            momentum = 'surging'
        elif velocity_ratio >= 1.5:
            momentum = 'rising'
        elif velocity_ratio <= 0.5:
            momentum = 'fading'
        else:
            momentum = 'steady'

        return {
            'success': True,
            'ticker': ticker,
            'mentions_today': today_count,
            'mentions_trailing_week': week_count,
            'trailing_week_daily_avg': round(week_daily_avg, 2),
            'velocity_ratio': round(velocity_ratio, 2),
            'momentum': momentum,
            'timestamp': datetime.now().isoformat(),
            'source': 'Reddit mention velocity',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error computing Reddit momentum for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Reddit mention velocity',
        }


def get_search_interest(ticker: str, company_name: str = "") -> Dict[str, Any]:
    """Google Trends search interest over the last 90 days (optional, best-effort)."""
    ticker = ticker.upper().strip()
    query_term = company_name or ticker

    try:
        from pytrends.request import TrendReq  # optional dependency
    except ImportError:
        return {
            'success': False,
            'error': 'pytrends not installed - run `pip install pytrends` to enable Google Trends data',
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Trends',
        }

    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(5, 15))
        pytrends.build_payload([query_term], timeframe='today 3-m')
        df = pytrends.interest_over_time()

        if df is None or df.empty:
            return {
                'success': True,
                'ticker': ticker,
                'series': [],
                'trend_direction': 'unknown',
                'note': 'No Google Trends data returned for this term',
                'timestamp': datetime.now().isoformat(),
                'source': 'Google Trends',
            }

        series = [
            {'date': str(idx.date()), 'interest': int(row[query_term])}
            for idx, row in df.iterrows()
        ]

        recent_avg = sum(p['interest'] for p in series[-7:]) / max(1, len(series[-7:]))
        earlier_avg = sum(p['interest'] for p in series[:7]) / max(1, len(series[:7]))
        if earlier_avg == 0:
            trend_direction = 'rising' if recent_avg > 0 else 'flat'
        else:
            change = (recent_avg - earlier_avg) / earlier_avg
            trend_direction = 'rising' if change > 0.15 else 'falling' if change < -0.15 else 'flat'

        return {
            'success': True,
            'ticker': ticker,
            'query_term': query_term,
            'series': series,
            'recent_week_avg_interest': round(recent_avg, 1),
            'trend_direction': trend_direction,
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Trends',
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error fetching Google Trends data for {query_term}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Google Trends',
        }


def get_social_trends(ticker: str, company_name: str = "") -> Dict[str, Any]:
    """Combined social/search momentum snapshot."""
    reddit_momentum = get_reddit_momentum(ticker)
    search_interest = get_search_interest(ticker, company_name)
    return {
        'ticker': ticker.upper().strip(),
        'reddit_momentum': reddit_momentum,
        'search_interest': search_interest,
        'timestamp': datetime.now().isoformat(),
    }


if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"Testing social trends scraper for {test_ticker}...")
    result = get_social_trends(test_ticker, "Apple")
    print(result['reddit_momentum'].get('momentum'), result['search_interest'].get('trend_direction'))
