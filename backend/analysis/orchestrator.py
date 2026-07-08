# analysis/orchestrator.py - Full multi-source analysis orchestration
"""
Fans out to every data source (Yahoo/Reddit/Twitter/SEC/Congress/GDELT/social
momentum) in parallel with a thread pool since they're all independent I/O
calls, blends sentiment across sources with the ML sentiment engine, and
assembles fundamentals + SWOT + the composite score into one response for
the `/api/full-analysis` endpoint.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from datetime import datetime

from scraping.yahoo import scrape_yahoo_stock
from scraping.reddit import scrape_reddit_stock
from scraping.twitter import scrape_twitter_stock
from scraping.insider_trading import get_congressional_trades
from scraping.geopolitical import get_geopolitical_context
from scraping.social_trends import get_social_trends

from analysis.ml_sentiment import classify_batch
from analysis.fundamentals import get_fundamental_analysis
from analysis.swot import generate_swot
from analysis.composite import compute_composite_score, DEFAULT_WEIGHTS

SOURCE_RELIABILITY_WEIGHTS = {'yahoo_finance': 0.5, 'reddit': 0.3, 'twitter': 0.2}


def _sentiment_for_yahoo(yahoo_data: Dict[str, Any]) -> Dict[str, Any]:
    if not yahoo_data.get('success'):
        return classify_batch([])
    headlines = yahoo_data.get('headlines', [])
    texts = [f"{h.get('title', '')} {h.get('summary', '')}" for h in headlines]
    return classify_batch(texts)


def _sentiment_for_reddit(reddit_data: Dict[str, Any]) -> Dict[str, Any]:
    if not reddit_data.get('success'):
        return classify_batch([])
    posts = reddit_data.get('posts', [])
    texts = [f"{p.get('title', '')} {p.get('text', '')}" for p in posts]
    weights = [max(1.0, min(10.0, p.get('score', 1) / 10)) for p in posts]
    return classify_batch(texts, weights)


def _sentiment_for_twitter(twitter_data: Dict[str, Any]) -> Dict[str, Any]:
    if not twitter_data.get('success'):
        return classify_batch([])
    tweets = twitter_data.get('tweets', [])
    texts = [t.get('text', '') for t in tweets]
    weights = [max(1.0, min(5.0, (t.get('likes', 0) + t.get('retweets', 0)) / 100)) for t in tweets]
    return classify_batch(texts, weights)


def _blend_sentiment(per_source: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    weighted_sum = 0.0
    weight_total = 0.0
    for source, weight in SOURCE_RELIABILITY_WEIGHTS.items():
        result = per_source.get(source)
        if result and result.get('n', 0) > 0:
            weighted_sum += result['overall_compound'] * weight
            weight_total += weight

    if weight_total == 0:
        return {'overall_label': 'neutral', 'overall_compound': 0.0, 'n_sources': 0}

    compound = round(weighted_sum / weight_total, 4)
    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'

    return {
        'overall_label': label,
        'overall_compound': compound,
        'n_sources': sum(1 for r in per_source.values() if r and r.get('n', 0) > 0),
    }


def build_full_analysis(ticker: str, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    ticker = ticker.upper().strip()

    # Yahoo first (cheap, single call) so we have a company name for the
    # geopolitical/social-trend searches; everything else fans out in parallel.
    yahoo_data = scrape_yahoo_stock(ticker)
    company_name = (yahoo_data.get('stock_data') or {}).get('company_name', ticker) if yahoo_data.get('success') else ticker

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            'reddit': executor.submit(scrape_reddit_stock, ticker),
            'twitter': executor.submit(scrape_twitter_stock, ticker),
            'fundamentals': executor.submit(get_fundamental_analysis, ticker),
            'insider': executor.submit(get_congressional_trades, ticker),
            'geopolitical': executor.submit(get_geopolitical_context, ticker, company_name),
            'social_trends': executor.submit(get_social_trends, ticker, company_name),
        }
        results = {name: future.result() for name, future in futures.items()}

    reddit_data = results['reddit']
    twitter_data = results['twitter']
    fundamentals = results['fundamentals']
    insider = results['insider']
    geopolitical = results['geopolitical']
    social_trends = results['social_trends']

    sentiment_by_source = {
        'yahoo_finance': _sentiment_for_yahoo(yahoo_data),
        'reddit': _sentiment_for_reddit(reddit_data),
        'twitter': _sentiment_for_twitter(twitter_data),
    }
    blended_sentiment = _blend_sentiment(sentiment_by_source)

    swot = generate_swot(
        ticker,
        fundamentals=fundamentals,
        sentiment_summary=blended_sentiment,
        insider=insider,
        geopolitical=geopolitical,
        social_trends=social_trends,
    )

    fundamentals_score = fundamentals.get('scoring', {}).get('overall_score') if fundamentals.get('success') else None
    insider_signal = insider.get('aggregate', {}).get('net_signal') if insider.get('success') else None
    geopolitical_exposure = geopolitical.get('geopolitical_exposure') if geopolitical.get('success') else None
    social_momentum = (social_trends.get('reddit_momentum') or {}).get('momentum') if social_trends.get('reddit_momentum', {}).get('success') else None

    composite = compute_composite_score(
        sentiment_compound=blended_sentiment.get('overall_compound'),
        fundamentals_score=fundamentals_score,
        insider_signal=insider_signal,
        geopolitical_exposure=geopolitical_exposure,
        social_momentum=social_momentum,
        weights=weights,
    )

    return {
        'ticker': ticker,
        'company_name': company_name,
        'raw_data': {
            'yahoo_finance': yahoo_data,
            'reddit': reddit_data,
            'twitter': twitter_data,
        },
        'fundamentals': fundamentals,
        'insider_trading': insider,
        'geopolitical': geopolitical,
        'social_trends': social_trends,
        'sentiment': {
            'by_source': sentiment_by_source,
            'blended': blended_sentiment,
        },
        'swot': swot,
        'composite_score': composite,
        'weights_used': composite.get('weights_used', DEFAULT_WEIGHTS),
        'timestamp': datetime.now().isoformat(),
        'api_version': '3.0',
    }
