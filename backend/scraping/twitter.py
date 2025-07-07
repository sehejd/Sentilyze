# scraping/twitter.py - Twitter/X scraping module
"""
Twitter/X scraper for stock-related tweets and sentiment.
This module provides functions to scrape tweets about stocks.
Note: Real Twitter API requires authentication. This provides mock data for development.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import random
import time


def scrape_twitter_stock(ticker: str) -> Dict[str, Any]:
    """
    Scrape Twitter/X posts related to a stock ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing tweets and metadata
    """
    ticker = ticker.upper().strip()
    
    try:
        # For now, we'll generate mock Twitter data
        # In production, you would use the Twitter API v2 with proper authentication
        
        mock_tweets = _generate_mock_tweets(ticker)
        
        return {
            'success': True,
            'tweets': mock_tweets,
            'total_found': len(mock_tweets),
            'timestamp': datetime.now().isoformat(),
            'source': 'Twitter/X',
            'note': 'Mock data - replace with real Twitter API implementation'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error scraping Twitter for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Twitter/X'
        }


def _generate_mock_tweets(ticker: str) -> List[Dict[str, Any]]:
    """
    Generate mock tweet data for development and testing.
    Replace this with real Twitter API calls in production.
    """
    
    # Mock tweet templates
    tweet_templates = [
        f"Just bought more ${ticker} shares! 🚀 #investing #stocks",
        f"${ticker} earnings report coming up next week. Expecting big things! 📈",
        f"Why is ${ticker} down today? Market manipulation? 🤔",
        f"${ticker} to the moon! 🌙 Diamond hands! 💎🙌",
        f"Thinking of selling my ${ticker} position. Thoughts? 🤷‍♂️",
        f"${ticker} breaking resistance levels! Bull run incoming? 🐂",
        f"${ticker} quarterly results exceeded expectations. Bullish! 📊",
        f"Red day for ${ticker} but I'm staying strong. HODL! 💪",
        f"${ticker} CEO announces new partnership. Stock should pump! 🎯",
        f"Technical analysis shows ${ticker} forming cup and handle pattern 📈",
        f"${ticker} short interest is high. Squeeze potential? 🤏",
        f"Bought the ${ticker} dip today. Thanks for the discount! 🛒",
        f"${ticker} insider buying activity spotted. Bullish signal? 👀",
        f"${ticker} revenue growth impressive this quarter. Long term hold! ⏰",
        f"Market volatility affecting ${ticker} but fundamentals remain strong 💪"
    ]
    
    # Mock sentiment indicators
    sentiments = ['positive', 'negative', 'neutral']
    sentiment_weights = [0.4, 0.3, 0.3]  # Slightly more positive bias
    
    # Mock user types
    user_types = [
        'financial_analyst', 'retail_trader', 'institutional', 
        'influencer', 'regular_user', 'bot'
    ]
    
    mock_tweets = []
    num_tweets = random.randint(15, 25)
    
    for i in range(num_tweets):
        # Random timestamp within last 24 hours
        hours_ago = random.randint(1, 24)
        tweet_time = datetime.now() - timedelta(hours=hours_ago)
        
        # Select random template and sentiment
        tweet_text = random.choice(tweet_templates)
        sentiment = random.choices(sentiments, weights=sentiment_weights)[0]
        
        # Mock engagement metrics
        likes = random.randint(0, 1000)
        retweets = random.randint(0, likes // 3)
        replies = random.randint(0, likes // 5)
        
        tweet = {
            'id': f"mock_tweet_{i}_{int(time.time())}",
            'text': tweet_text,
            'user_handle': f"@trader_{random.randint(1000, 9999)}",
            'user_type': random.choice(user_types),
            'user_followers': random.randint(100, 50000),
            'likes': likes,
            'retweets': retweets,
            'replies': replies,
            'sentiment_indicator': sentiment,
            'timestamp': tweet_time.isoformat(),
            'url': f"https://twitter.com/trader_{random.randint(1000, 9999)}/status/{random.randint(1000000000000000000, 9999999999999999999)}",
            'source': 'Twitter/X',
            'is_mock': True
        }
        
        mock_tweets.append(tweet)
    
    # Sort by engagement (likes + retweets)
    mock_tweets.sort(key=lambda x: x['likes'] + x['retweets'], reverse=True)
    
    return mock_tweets


def setup_twitter_api():
    """
    Placeholder for real Twitter API setup.
    In production, implement Twitter API v2 authentication here.
    """
    return {
        'setup': False,
        'message': 'Replace with real Twitter API credentials and setup'
    }


# Real Twitter API implementation template (commented out)
"""
def scrape_twitter_stock_real(ticker: str, api_key: str, api_secret: str, 
                             bearer_token: str) -> Dict[str, Any]:
    '''
    Real Twitter API implementation.
    Requires Twitter API v2 credentials.
    '''
    import tweepy
    
    # Setup Twitter API client
    client = tweepy.Client(bearer_token=bearer_token)
    
    try:
        # Search for tweets mentioning the ticker
        query = f"${ticker} OR #{ticker} -is:retweet lang:en"
        
        tweets = tweepy.Paginator(
            client.search_recent_tweets,
            query=query,
            tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
            max_results=100
        ).flatten(limit=100)
        
        processed_tweets = []
        for tweet in tweets:
            processed_tweet = {
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat(),
                'author_id': tweet.author_id,
                'metrics': tweet.public_metrics,
                'source': 'Twitter/X'
            }
            processed_tweets.append(processed_tweet)
        
        return {
            'success': True,
            'tweets': processed_tweets,
            'total_found': len(processed_tweets),
            'timestamp': datetime.now().isoformat(),
            'source': 'Twitter/X'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error with Twitter API: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Twitter/X'
        }
"""


if __name__ == "__main__":
    # Test the scraper
    test_ticker = "AAPL"
    print(f"Testing Twitter scraper for {test_ticker}...")
    result = scrape_twitter_stock(test_ticker)
    
    if result['success']:
        print("✅ Success!")
        print(f"Generated {result['total_found']} mock tweets")
        print("Top 5 tweets by engagement:")
        for i, tweet in enumerate(result['tweets'][:5]):
            engagement = tweet['likes'] + tweet['retweets']
            print(f"{i+1}. {tweet['text'][:50]}... (Engagement: {engagement})")
    else:
        print("❌ Failed!")
        print(f"Error: {result['error']}")