# scraping/reddit.py - Reddit scraping module
"""
Reddit scraper for stock-related discussions and sentiment.
This module provides functions to scrape Reddit posts about stocks from relevant subreddits.
"""

import requests
from typing import Dict, List, Any
from datetime import datetime
import time
import re


def scrape_reddit_stock(ticker: str) -> Dict[str, Any]:
    """
    Scrape Reddit posts and comments related to a stock ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing Reddit posts, comments, and metadata
    """
    ticker = ticker.upper().strip()
    
    try:
        # List of relevant subreddits for stock discussions
        subreddits = [
            'stocks',
            'investing',
            'wallstreetbets',
            'SecurityAnalysis',
            'ValueInvesting',
            'StockMarket'
        ]
        
        all_posts = []
        
        # Search for posts mentioning the ticker across multiple subreddits
        for subreddit in subreddits:
            try:
                # Use Reddit's JSON API (no authentication needed for public posts)
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': f"${ticker} OR {ticker}",
                    'sort': 'new',
                    'limit': 10,
                    'restrict_sr': 'on',
                    't': 'week'  # Last week's posts
                }
                
                headers = {
                    'User-Agent': 'SentilyzeBot/1.0 (Stock Analysis Tool)'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for post in data.get('data', {}).get('children', []):
                        post_data = post.get('data', {})
                        
                        # Extract relevant information
                        reddit_post = {
                            'title': post_data.get('title', ''),
                            'text': post_data.get('selftext', ''),
                            'score': post_data.get('score', 0),
                            'upvote_ratio': post_data.get('upvote_ratio', 0),
                            'num_comments': post_data.get('num_comments', 0),
                            'subreddit': f"r/{subreddit}",
                            'author': post_data.get('author', '[deleted]'),
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'timestamp': datetime.fromtimestamp(
                                post_data.get('created_utc', time.time())
                            ).isoformat(),
                            'source': 'Reddit'
                        }
                        
                        # Only include posts that actually mention the ticker
                        combined_text = f"{reddit_post['title']} {reddit_post['text']}".upper()
                        if (f"${ticker}" in combined_text or 
                            re.search(rf'\b{ticker}\b', combined_text)):
                            all_posts.append(reddit_post)
                
                # Add delay to be respectful to Reddit's servers
                time.sleep(0.5)
                
            except Exception as subreddit_error:
                print(f"Error scraping r/{subreddit}: {str(subreddit_error)}")
                continue
        
        # Sort posts by score (popularity) and recency
        all_posts.sort(key=lambda x: (x['score'], x['timestamp']), reverse=True)
        
        # Limit to top 20 posts
        top_posts = all_posts[:20]
        
        return {
            'success': True,
            'posts': top_posts,
            'total_found': len(all_posts),
            'subreddits_searched': subreddits,
            'timestamp': datetime.now().isoformat(),
            'source': 'Reddit'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error scraping Reddit for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Reddit'
        }


def get_reddit_sentiment_keywords() -> List[str]:
    """
    Return common sentiment keywords used in stock discussions.
    """
    return [
        # Positive keywords
        'bullish', 'moon', 'rocket', 'buy', 'hold', 'long', 'calls', 
        'pump', 'squeeze', 'diamond hands', 'to the moon', 'hodl',
        
        # Negative keywords  
        'bearish', 'crash', 'sell', 'short', 'puts', 'dump', 'paper hands',
        'bag holder', 'rekt', 'loss porn'
    ]


if __name__ == "__main__":
    # Test the scraper
    test_ticker = "AAPL"
    print(f"Testing Reddit scraper for {test_ticker}...")
    result = scrape_reddit_stock(test_ticker)
    
    if result['success']:
        print("✅ Success!")
        print(f"Found {result['total_found']} total posts")
        print(f"Top {len(result['posts'])} posts:")
        for i, post in enumerate(result['posts'][:5]):
            print(f"{i+1}. {post['title']} (Score: {post['score']}, r/{post['subreddit']})")
    else:
        print("❌ Failed!")
        print(f"Error: {result['error']}")