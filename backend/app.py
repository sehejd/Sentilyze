# app.py - Main Flask application with AI-powered stock analysis
"""
Sentilyze Backend API - AI-powered stock sentiment analysis
Integrates data from Yahoo Finance, Reddit, and Twitter for comprehensive analysis.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from typing import Dict, Any
import traceback

# Add the parent directory to the path so we can import from scraping and analysis
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import scrapers
from scraping.yahoo import scrape_yahoo_stock, get_stock_data
from scraping.reddit import scrape_reddit_stock
from scraping.twitter import scrape_twitter_stock

# Import AI analyzer
from analysis.ai_analyzer import AIStockAnalyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize AI analyzer
ai_analyzer = AIStockAnalyzer()


@app.route('/api/analyze', methods=['GET'])
def comprehensive_analysis():
    """
    Main endpoint for comprehensive stock analysis using AI.
    Scrapes data from all sources and generates AI-powered insights.
    
    Example: /api/analyze?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    ticker = ticker.upper().strip()
    
    try:
        # Step 1: Scrape data from all sources
        print(f"🔍 Starting comprehensive analysis for {ticker}...")
        
        # Scrape Yahoo Finance
        print("📊 Scraping Yahoo Finance...")
        yahoo_data = scrape_yahoo_stock(ticker)
        
        # Scrape Reddit
        print("🤖 Scraping Reddit...")
        reddit_data = scrape_reddit_stock(ticker)
        
        # Scrape Twitter
        print("🐦 Scraping Twitter...")
        twitter_data = scrape_twitter_stock(ticker)
        
        # Step 2: AI Analysis
        print("🧠 Performing AI analysis...")
        ai_result = ai_analyzer.analyze_stock_sentiment(
            yahoo_data, reddit_data, twitter_data, ticker
        )
        
        if not ai_result['success']:
            return jsonify({
                'error': 'AI analysis failed',
                'details': ai_result.get('error', 'Unknown error')
            }), 500
        
        # Step 3: Compile comprehensive response
        response = {
            'ticker': ticker,
            'analysis': ai_result['report'],
            'raw_data': {
                'yahoo_finance': yahoo_data,
                'reddit': reddit_data,
                'twitter': twitter_data
            },
            'timestamp': ai_result['timestamp'],
            'api_version': '2.0'
        }
        
        print(f"✅ Analysis complete for {ticker}")
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Comprehensive analysis failed for {ticker}: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500


@app.route('/api/yahoo', methods=['GET'])
def yahoo_endpoint():
    """
    Endpoint to get stock data from Yahoo Finance only.
    Example: /api/yahoo?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    try:
        # Use legacy function for backward compatibility
        data = get_stock_data(ticker)
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': f'No data found for ticker {ticker}'}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/yahoo/full', methods=['GET'])
def yahoo_full_endpoint():
    """
    Endpoint to get comprehensive Yahoo Finance data including headlines.
    Example: /api/yahoo/full?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    try:
        data = scrape_yahoo_stock(ticker)
        if data['success']:
            return jsonify(data)
        else:
            return jsonify({'error': data.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/reddit', methods=['GET'])
def reddit_endpoint():
    """
    Endpoint to get Reddit sentiment data.
    Example: /api/reddit?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    try:
        data = scrape_reddit_stock(ticker)
        if data['success']:
            # Convert to frontend-compatible format
            headlines = []
            for post in data['posts']:
                headline = {
                    'text': f"{post['title']} - {post['text'][:100]}...",
                    'sentiment': _simple_sentiment_analysis(post['title'] + ' ' + post['text']),
                    'timestamp': post['timestamp'],
                    'source': 'Reddit'
                }
                headlines.append(headline)
            
            return jsonify({
                'ticker': ticker.upper(),
                'headlines': headlines
            })
        else:
            return jsonify({'error': data.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/twitter', methods=['GET'])
def twitter_endpoint():
    """
    Endpoint to get Twitter sentiment data.
    Example: /api/twitter?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    try:
        data = scrape_twitter_stock(ticker)
        if data['success']:
            # Convert to frontend-compatible format
            headlines = []
            for tweet in data['tweets']:
                headline = {
                    'text': tweet['text'],
                    'sentiment': tweet.get('sentiment_indicator', 'neutral'),
                    'timestamp': tweet['timestamp'],
                    'source': 'Twitter'
                }
                headlines.append(headline)
            
            return jsonify({
                'ticker': ticker.upper(),
                'headlines': headlines
            })
        else:
            return jsonify({'error': data.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/sentiment', methods=['GET'])
def sentiment_analysis_endpoint():
    """
    Endpoint for AI-powered sentiment analysis only (no raw data).
    Example: /api/sentiment?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    try:
        # Quick scrape from all sources
        yahoo_data = scrape_yahoo_stock(ticker)
        reddit_data = scrape_reddit_stock(ticker)
        twitter_data = scrape_twitter_stock(ticker)
        
        # AI analysis
        ai_result = ai_analyzer.analyze_stock_sentiment(
            yahoo_data, reddit_data, twitter_data, ticker
        )
        
        if ai_result['success']:
            return jsonify({
                'ticker': ticker.upper(),
                'sentiment_analysis': ai_result['report'],
                'timestamp': ai_result['timestamp']
            })
        else:
            return jsonify({'error': ai_result.get('error', 'Analysis failed')}), 500
            
    except Exception as e:
        return jsonify({'error': f'Sentiment analysis failed: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with system status."""
    try:
        # Test each scraper
        test_results = {
            'yahoo': 'ok',
            'reddit': 'ok', 
            'twitter': 'ok',
            'ai_analyzer': 'ok'
        }
        
        # Quick test of each module
        try:
            scrape_yahoo_stock('AAPL')
        except:
            test_results['yahoo'] = 'error'
            
        try:
            scrape_reddit_stock('AAPL')
        except:
            test_results['reddit'] = 'error'
            
        try:
            scrape_twitter_stock('AAPL')
        except:
            test_results['twitter'] = 'error'
        
        return jsonify({
            'status': 'healthy',
            'message': 'Sentilyze API is running',
            'modules': test_results,
            'version': '2.0',
            'features': [
                'Yahoo Finance scraping',
                'Reddit sentiment analysis', 
                'Twitter sentiment analysis',
                'AI-powered comprehensive analysis'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }), 500


def _simple_sentiment_analysis(text: str) -> str:
    """Simple sentiment analysis for backward compatibility."""
    text = text.lower()
    positive_words = ['good', 'great', 'buy', 'moon', 'pump', 'bullish', 'up']
    negative_words = ['bad', 'sell', 'crash', 'dump', 'bearish', 'down']
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'


if __name__ == '__main__':
    print("🚀 Starting Sentilyze API Server...")
    print("📊 Yahoo Finance scraper: Ready")
    print("🤖 Reddit scraper: Ready") 
    print("🐦 Twitter scraper: Ready")
    print("🧠 AI Analyzer: Ready")
    print("🌐 Server starting on http://localhost:8000")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
