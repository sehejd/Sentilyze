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
from scraping.sec_edgar import get_recent_filings
from scraping.insider_trading import get_congressional_trades
from scraping.geopolitical import get_geopolitical_context
from scraping.social_trends import get_social_trends

# Import AI analyzer
from analysis.ai_analyzer import AIStockAnalyzer
from analysis.fundamentals import get_fundamental_analysis, evaluate_metric_checks, get_fundamentals
from analysis.swot import generate_swot
from analysis.composite import compute_composite_score
from analysis.orchestrator import build_full_analysis
from analysis.political_network import build_political_network
from analysis.political_web import build_political_web
from analysis.valuation import run_valuation
from analysis.peer_performance_model import run_peer_performance_analysis

# Import backtesting engine
from backtesting.engine import run_backtest
from backtesting.indicators import AVAILABLE_INDICATORS, OPERATORS

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


@app.route('/api/fundamentals', methods=['GET'])
def fundamentals_endpoint():
    """
    Fundamental analysis with a 0-100 score against configurable thresholds.
    Example: /api/fundamentals?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        result = get_fundamental_analysis(ticker)
        if result.get('success'):
            return jsonify(result)
        return jsonify({'error': result.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/sec/filings', methods=['GET'])
def sec_filings_endpoint():
    """
    Recent 10-Q/10-K quarterly & annual report metadata from SEC EDGAR.
    Example: /api/sec/filings?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        result = get_recent_filings(ticker)
        if result.get('success'):
            return jsonify(result)
        return jsonify({'error': result.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/insider', methods=['GET'])
def insider_endpoint():
    """
    Congressional (political) stock trading disclosures for a ticker.
    Example: /api/insider?ticker=AAPL&days=365
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    days_back = request.args.get('days', 365, type=int)

    try:
        result = get_congressional_trades(ticker, days_back=days_back)
        if result.get('success'):
            return jsonify(result)
        return jsonify({'error': result.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/geopolitical', methods=['GET'])
def geopolitical_endpoint():
    """
    Geopolitical news exposure (trade policy, sanctions, conflict, elections,
    monetary policy, supply chain) for a ticker via the GDELT Project.
    Example: /api/geopolitical?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    company_name = request.args.get('company_name', '')

    try:
        result = get_geopolitical_context(ticker, company_name)
        if result.get('success'):
            return jsonify(result)
        return jsonify({'error': result.get('error', 'Unknown error')}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/social-trends', methods=['GET'])
def social_trends_endpoint():
    """
    Social/search momentum: Reddit mention velocity + Google Trends interest.
    Example: /api/social-trends?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    company_name = request.args.get('company_name', '')

    try:
        return jsonify(get_social_trends(ticker, company_name))
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/swot', methods=['GET'])
def swot_endpoint():
    """
    Full SWOT analysis assembled from fundamentals, blended sentiment,
    insider trading, geopolitical exposure, and social momentum.
    Example: /api/swot?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        full = build_full_analysis(ticker)
        return jsonify(full['swot'])
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/composite', methods=['GET'])
def composite_endpoint():
    """
    Weighted composite "Sentilyze Score" (0-100) combining sentiment,
    fundamentals, insider trading, geopolitical exposure, and social momentum.
    Override default weights with query params, e.g.
    /api/composite?ticker=AAPL&w_sentiment=0.4&w_fundamentals=0.4&w_insider=0.1&w_geopolitical=0.05&w_social_momentum=0.05
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    weight_overrides = {}
    for key, param in [('sentiment', 'w_sentiment'), ('fundamentals', 'w_fundamentals'),
                        ('insider', 'w_insider'), ('geopolitical', 'w_geopolitical'),
                        ('social_momentum', 'w_social_momentum')]:
        value = request.args.get(param, type=float)
        if value is not None:
            weight_overrides[key] = value

    try:
        full = build_full_analysis(ticker, weights=weight_overrides or None)
        return jsonify({
            'ticker': full['ticker'],
            'composite_score': full['composite_score'],
            'sentiment': full['sentiment']['blended'],
            'timestamp': full['timestamp'],
        })
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/full-analysis', methods=['GET'])
def full_analysis_endpoint():
    """
    Comprehensive dashboard endpoint: Yahoo/Reddit/Twitter + fundamentals +
    insider trading + geopolitical exposure + social momentum + ML sentiment
    + SWOT + composite score, all in one call. This is what the main
    frontend dashboard uses.
    Example: /api/full-analysis?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    weight_overrides = {}
    for key, param in [('sentiment', 'w_sentiment'), ('fundamentals', 'w_fundamentals'),
                        ('insider', 'w_insider'), ('geopolitical', 'w_geopolitical'),
                        ('social_momentum', 'w_social_momentum')]:
        value = request.args.get(param, type=float)
        if value is not None:
            weight_overrides[key] = value

    try:
        return jsonify(build_full_analysis(ticker, weights=weight_overrides or None))
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Full analysis failed for {ticker}: {str(e)}'}), 500


@app.route('/api/political-network', methods=['GET'])
def political_network_endpoint():
    """
    "Deeper dive" political network: what bills the company lobbies for, who
    sponsors those bills, the company's named executives, what politicians
    those executives personally donate to (FEC), and any possible overlaps
    with the ticker's congressional stock-trading disclosures.

    Not bundled into /api/full-analysis since it fans out to several more
    slow public APIs (Senate LDA, Congress.gov, FEC) - call on demand.

    Example: /api/political-network?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    company_name = request.args.get('company_name', '')
    if not company_name:
        yahoo_data = scrape_yahoo_stock(ticker)
        company_name = (yahoo_data.get('stock_data') or {}).get('company_name', ticker) if yahoo_data.get('success') else ticker

    try:
        return jsonify(build_political_network(ticker, company_name))
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Political network lookup failed for {ticker}: {str(e)}'}), 500


@app.route('/api/political-web', methods=['GET'])
def political_web_endpoint():
    """
    Multi-company political network graph: every disclosed politician<->
    company congressional trading relationship (the full public STOCK Act
    dataset), optionally enriched with lobbying/bill-sponsor and executive-
    donation edges for the most active companies.

    Query params (all optional):
      days_back              lookback window for trading data, default 730
      max_trading_edges      cap on politician<->company trading edges, default 150
      max_lobbying_companies cap on companies enriched with lobbying/bills, default 20 (0 disables)
      max_donation_companies cap on companies enriched with exec donations, default 0 (opt-in, slowest tier)

    Example: /api/political-web?max_lobbying_companies=15&max_donation_companies=5
    """
    days_back = request.args.get('days_back', 730, type=int)
    max_trading_edges = request.args.get('max_trading_edges', 150, type=int)
    max_lobbying_companies = request.args.get('max_lobbying_companies', 20, type=int)
    max_donation_companies = request.args.get('max_donation_companies', 0, type=int)

    try:
        result = build_political_web(
            days_back=days_back,
            max_trading_edges=max_trading_edges,
            max_lobbying_companies=max_lobbying_companies,
            max_donation_companies=max_donation_companies,
        )
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Unknown error')}), 502
        return jsonify(result)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Political web build failed: {str(e)}'}), 500


@app.route('/api/valuation', methods=['GET'])
def valuation_endpoint():
    """
    Multi-method fundamental valuation: DCF, comparable company analysis,
    dividend discount model, Graham number, and asset-based valuation.

    Optional: peer_tickers=TICK1,TICK2,... to override the default sector peer list.

    Example: /api/valuation?ticker=AAPL
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    peer_tickers = request.args.get('peer_tickers')
    peer_list = [t.strip().upper() for t in peer_tickers.split(',') if t.strip()] if peer_tickers else None

    try:
        result = run_valuation(ticker, peer_tickers=peer_list)
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Unknown error')}), 404
        return jsonify(result)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Valuation failed for {ticker}: {str(e)}'}), 500


@app.route('/api/peer-performance', methods=['GET'])
def peer_performance_endpoint():
    """
    Cross-sectional logistic regression: compares the ticker's fundamentals,
    news sentiment, and congressional trading signal against sector peers,
    labeled by trailing price return vs the sector median. See
    analysis/peer_performance_model.py for the methodology caveats - this is
    a snapshot comparison, not a historical panel model.

    Optional: lookback_months (default 12), peer_tickers=TICK1,TICK2,...

    Example: /api/peer-performance?ticker=AAPL&lookback_months=12
    """
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    lookback_months = request.args.get('lookback_months', 12, type=int)
    peer_tickers = request.args.get('peer_tickers')
    peer_list = [t.strip().upper() for t in peer_tickers.split(',') if t.strip()] if peer_tickers else None

    try:
        result = run_peer_performance_analysis(ticker, lookback_months=lookback_months, peer_tickers=peer_list)
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Unknown error')}), 404
        return jsonify(result)
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Peer performance analysis failed for {ticker}: {str(e)}'}), 500


@app.route('/api/backtest/indicators', methods=['GET'])
def backtest_indicators_endpoint():
    """Metadata for the backtest rule builder: available indicator fields, operators, and default fundamental thresholds."""
    from analysis.fundamentals import DEFAULT_THRESHOLDS
    return jsonify({
        'indicators': AVAILABLE_INDICATORS,
        'operators': OPERATORS,
        'fundamental_metrics': {
            name: {'direction': cfg['direction'], 'bands': cfg['bands']}
            for name, cfg in DEFAULT_THRESHOLDS.items()
        },
    })


@app.route('/api/backtest', methods=['POST'])
def backtest_endpoint():
    """
    Run a rule-based backtest over historical price data.

    Body:
    {
      "ticker": "AAPL",
      "start": "2022-01-01",
      "end": "2024-01-01",              // optional, defaults to latest
      "entry_rules": [{"field": "rsi_14", "operator": "<", "value": 30}],
      "exit_rules": [{"field": "rsi_14", "operator": ">", "value": 70}],
      "initial_capital": 10000,          // optional, default 10000
      "position_size_pct": 1.0,          // optional, fraction of cash per trade, default 1.0
      "stop_loss_pct": 10,               // optional
      "take_profit_pct": 20,             // optional
      "fundamental_gate": {              // optional static fundamental filter
        "enabled": true,
        "checks": [{"metric": "pe_ratio", "operator": "<", "value": 25}]
      }
    }
    """
    body = request.get_json(silent=True) or {}
    ticker = body.get('ticker')
    start = body.get('start')

    if not ticker or not start:
        return jsonify({'error': 'ticker and start are required'}), 400

    entry_gate_passed = True
    entry_gate_note = None

    fundamental_gate = body.get('fundamental_gate') or {}
    if fundamental_gate.get('enabled') and fundamental_gate.get('checks'):
        fundamentals = get_fundamentals(ticker)
        if not fundamentals.get('success'):
            entry_gate_passed = False
            entry_gate_note = f"Fundamental gate failed: could not fetch fundamentals ({fundamentals.get('error')})"
        else:
            gate_result = evaluate_metric_checks(fundamentals['metrics'], fundamental_gate['checks'])
            entry_gate_passed = gate_result['passed']
            entry_gate_note = (
                f"Static fundamental gate evaluated against current data: "
                f"{'passed' if entry_gate_passed else 'failed'} ({gate_result['checks']})"
            )

    try:
        result = run_backtest(
            ticker=ticker,
            start=start,
            end=body.get('end'),
            entry_rules=body.get('entry_rules', []),
            exit_rules=body.get('exit_rules', []),
            initial_capital=float(body.get('initial_capital', 10000)),
            position_size_pct=float(body.get('position_size_pct', 1.0)),
            stop_loss_pct=body.get('stop_loss_pct'),
            take_profit_pct=body.get('take_profit_pct'),
            entry_gate_passed=entry_gate_passed,
            entry_gate_note=entry_gate_note,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': f'Backtest failed: {str(e)}'}), 500


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
            'version': '3.0',
            'features': [
                'Yahoo Finance scraping',
                'Reddit sentiment analysis',
                'Twitter sentiment analysis',
                'ML sentiment ensemble (VADER + TextBlob, optional FinBERT)',
                'SEC EDGAR fundamentals & quarterly/annual filings',
                'Congressional (political) insider trading signal',
                'Geopolitical risk exposure (GDELT)',
                'Social/search momentum (Reddit velocity + Google Trends)',
                'SWOT analysis generator',
                'Composite Sentilyze Score',
                'Rule-based backtesting engine',
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
