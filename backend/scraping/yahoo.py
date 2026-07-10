# scraping/yahoo.py - Yahoo Finance scraping module
"""
Yahoo Finance scraper for stock data and news headlines.
This module provides functions to scrape stock information and related news from Yahoo Finance.
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

from utils.yf_client import get_info, with_retry


def scrape_yahoo_stock(ticker: str) -> Dict[str, Any]:
    """
    Scrape stock data and news headlines from Yahoo Finance.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing stock data, headlines, and metadata
    """
    ticker = ticker.upper().strip()
    
    try:
        # Get stock data using yfinance (cached + retrying - see utils/yf_client.py)
        info = get_info(ticker)
        if not info:
            return {
                'success': False,
                'error': f"No data found for ticker {ticker} (Yahoo Finance unavailable or rate limited)",
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }

        # Get recent news
        news = with_retry(lambda: yf.Ticker(ticker).news, what=f".news for {ticker}")
        
        # Extract basic stock information
        stock_data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
            'previous_close': info.get('previousClose', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'avg_volume': info.get('averageVolume', 'N/A'),
        }
        
        # Calculate price change
        if (stock_data['current_price'] != 'N/A' and 
            stock_data['previous_close'] != 'N/A'):
            try:
                price_change = stock_data['current_price'] - stock_data['previous_close']
                percent_change = (price_change / stock_data['previous_close']) * 100
                stock_data['change'] = f"{price_change:+.2f}"
                stock_data['percent_change'] = f"{percent_change:+.2f}%"
            except (TypeError, ValueError):
                stock_data['change'] = 'N/A'
                stock_data['percent_change'] = 'N/A'
        else:
            stock_data['change'] = 'N/A'
            stock_data['percent_change'] = 'N/A'
        
        # Process news headlines
        headlines = []
        for article in news[:10]:  # Limit to 10 most recent articles
            headline_data = {
                'title': article.get('title', ''),
                'summary': article.get('summary', ''),
                'link': article.get('link', ''),
                'publisher': article.get('publisher', 'Yahoo Finance'),
                'timestamp': datetime.fromtimestamp(
                    article.get('providerPublishTime', time.time())
                ).isoformat(),
                'source': 'Yahoo Finance'
            }
            headlines.append(headline_data)
        
        return {
            'success': True,
            'stock_data': stock_data,
            'headlines': headlines,
            'timestamp': datetime.now().isoformat(),
            'source': 'Yahoo Finance'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error scraping Yahoo Finance for {ticker}: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'source': 'Yahoo Finance'
        }


def get_stock_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    Returns only basic stock data without headlines.
    """
    result = scrape_yahoo_stock(ticker)
    if result['success']:
        return result['stock_data']
    return None


if __name__ == "__main__":
    # Test the scraper
    test_ticker = "AAPL"
    print(f"Testing Yahoo Finance scraper for {test_ticker}...")
    result = scrape_yahoo_stock(test_ticker)
    
    if result['success']:
        print("✅ Success!")
        print(f"Stock Data: {result['stock_data']}")
        print(f"Found {len(result['headlines'])} headlines")
        for i, headline in enumerate(result['headlines'][:3]):
            print(f"{i+1}. {headline['title']}")
    else:
        print("❌ Failed!")
        print(f"Error: {result['error']}")
   

  