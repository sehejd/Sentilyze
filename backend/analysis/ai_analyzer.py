# analysis/ai_analyzer.py - AI-powered stock analysis module
"""
AI-powered stock sentiment analysis and report generation.
This module processes scraped data and generates comprehensive stock analysis reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
import os
from dataclasses import dataclass
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class SentimentScore:
    """Data class for sentiment analysis results."""
    positive: float
    negative: float
    neutral: float
    overall: str
    confidence: float


class AIStockAnalyzer:
    """
    AI-powered stock analyzer that processes data from multiple sources
    and generates comprehensive reports.
    """
    
    def __init__(self):
        """Initialize the AI analyzer."""
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            print("Warning: GEMINI_API_KEY not found in environment variables")
            self.model = None
            
        self.sentiment_keywords = {
            'positive': [
                'bullish', 'buy', 'moon', 'rocket', 'pump', 'squeeze', 'hold', 'long',
                'diamond hands', 'hodl', 'calls', 'up', 'gain', 'profit', 'strong',
                'growth', 'earnings beat', 'upgrade', 'outperform', 'breakout'
            ],
            'negative': [
                'bearish', 'sell', 'crash', 'dump', 'short', 'puts', 'down', 'loss',
                'paper hands', 'weak', 'decline', 'miss', 'downgrade', 'underperform',
                'resistance', 'support broken', 'bear market', 'recession'
            ],
            'neutral': [
                'hold', 'watch', 'wait', 'sideways', 'consolidation', 'range bound',
                'market', 'analysis', 'technical', 'fundamental'
            ]
        }
    
    def analyze_stock_sentiment(
        self, 
        yahoo_data: Dict[str, Any],
        reddit_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
        ticker: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment across all data sources and generate a comprehensive report.
        
        Args:
            yahoo_data: Data from Yahoo Finance scraper
            reddit_data: Data from Reddit scraper
            twitter_data: Data from Twitter scraper
            ticker: Stock ticker symbol
        
        Returns:
            Comprehensive analysis report
        """
        
        try:
            # Analyze sentiment from each source
            yahoo_sentiment = self._analyze_yahoo_sentiment(yahoo_data)
            reddit_sentiment = self._analyze_reddit_sentiment(reddit_data)
            twitter_sentiment = self._analyze_twitter_sentiment(twitter_data)
            
            # Aggregate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(
                yahoo_sentiment, reddit_sentiment, twitter_sentiment
            )
            
            # Generate key insights
            key_insights = self._generate_key_insights(
                yahoo_data, reddit_data, twitter_data, overall_sentiment
            )
            
            # Generate projections
            projections = self._generate_projections(
                yahoo_data, overall_sentiment, key_insights
            )
            
            # Generate AI summary using Gemini
            ai_summary = self.generate_ai_summary(
                yahoo_data, reddit_data, twitter_data, ticker, {
                    'overall_sentiment': overall_sentiment,
                    'source_analysis': {
                        'yahoo_finance': yahoo_sentiment,
                        'reddit': reddit_sentiment,
                        'twitter': twitter_sentiment
                    }
                }
            )
            
            # Create comprehensive report
            report = {
                'ticker': ticker.upper(),
                'analysis_timestamp': datetime.now().isoformat(),
                'overall_sentiment': overall_sentiment,
                'source_analysis': {
                    'yahoo_finance': yahoo_sentiment,
                    'reddit': reddit_sentiment,
                    'twitter': twitter_sentiment
                },
                'key_insights': key_insights,
                'projections': projections,
                'summary': self._generate_executive_summary(
                    ticker, overall_sentiment, key_insights, projections
                ),
                'ai_summary': ai_summary,  # Add Gemini-generated summary
                'confidence_score': self._calculate_confidence_score(
                    yahoo_data, reddit_data, twitter_data
                ),
                'data_quality': self._assess_data_quality(
                    yahoo_data, reddit_data, twitter_data
                )
            }
            
            return {
                'success': True,
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error in AI analysis: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_yahoo_sentiment(self, yahoo_data: Dict[str, Any]) -> SentimentScore:
        """Analyze sentiment from Yahoo Finance headlines."""
        if not yahoo_data.get('success') or not yahoo_data.get('headlines'):
            return SentimentScore(0.33, 0.33, 0.34, 'neutral', 0.0)
        
        headlines = yahoo_data['headlines']
        sentiments = []
        
        for headline in headlines:
            text = f"{headline.get('title', '')} {headline.get('summary', '')}".lower()
            sentiment = self._classify_text_sentiment(text)
            sentiments.append(sentiment)
        
        return self._aggregate_sentiments(sentiments)
    
    def _analyze_reddit_sentiment(self, reddit_data: Dict[str, Any]) -> SentimentScore:
        """Analyze sentiment from Reddit posts."""
        if not reddit_data.get('success') or not reddit_data.get('posts'):
            return SentimentScore(0.33, 0.33, 0.34, 'neutral', 0.0)
        
        posts = reddit_data['posts']
        sentiments = []
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('text', '')}".lower()
            sentiment = self._classify_text_sentiment(text)
            # Weight by score (popularity)
            score_weight = max(1, min(10, post.get('score', 1) / 10))
            for _ in range(int(score_weight)):
                sentiments.append(sentiment)
        
        return self._aggregate_sentiments(sentiments)
    
    def _analyze_twitter_sentiment(self, twitter_data: Dict[str, Any]) -> SentimentScore:
        """Analyze sentiment from Twitter posts."""
        if not twitter_data.get('success') or not twitter_data.get('tweets'):
            return SentimentScore(0.33, 0.33, 0.34, 'neutral', 0.0)
        
        tweets = twitter_data['tweets']
        sentiments = []
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            sentiment = self._classify_text_sentiment(text)
            # Weight by engagement
            engagement = tweet.get('likes', 0) + tweet.get('retweets', 0)
            engagement_weight = max(1, min(5, engagement / 100))
            for _ in range(int(engagement_weight)):
                sentiments.append(sentiment)
        
        return self._aggregate_sentiments(sentiments)
    
    def _classify_text_sentiment(self, text: str) -> str:
        """Classify sentiment of a text using keyword matching."""
        positive_count = sum(1 for keyword in self.sentiment_keywords['positive'] 
                           if keyword in text)
        negative_count = sum(1 for keyword in self.sentiment_keywords['negative'] 
                           if keyword in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _aggregate_sentiments(self, sentiments: List[str]) -> SentimentScore:
        """Aggregate individual sentiment classifications."""
        if not sentiments:
            return SentimentScore(0.33, 0.33, 0.34, 'neutral', 0.0)
        
        total = len(sentiments)
        positive = sentiments.count('positive') / total
        negative = sentiments.count('negative') / total
        neutral = sentiments.count('neutral') / total
        
        if positive > negative and positive > neutral:
            overall = 'positive'
        elif negative > positive and negative > neutral:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        confidence = max(positive, negative, neutral)
        
        return SentimentScore(positive, negative, neutral, overall, confidence)
    
    def _calculate_overall_sentiment(
        self, 
        yahoo: SentimentScore, 
        reddit: SentimentScore, 
        twitter: SentimentScore
    ) -> Dict[str, Any]:
        """Calculate weighted overall sentiment across all sources."""
        
        # Weight sources (Yahoo Finance gets higher weight for reliability)
        weights = {'yahoo': 0.5, 'reddit': 0.3, 'twitter': 0.2}
        
        overall_positive = (
            yahoo.positive * weights['yahoo'] +
            reddit.positive * weights['reddit'] +
            twitter.positive * weights['twitter']
        )
        
        overall_negative = (
            yahoo.negative * weights['yahoo'] +
            reddit.negative * weights['reddit'] +
            twitter.negative * weights['twitter']
        )
        
        overall_neutral = (
            yahoo.neutral * weights['yahoo'] +
            reddit.neutral * weights['reddit'] +
            twitter.neutral * weights['twitter']
        )
        
        if overall_positive > overall_negative and overall_positive > overall_neutral:
            sentiment = 'positive'
        elif overall_negative > overall_positive and overall_negative > overall_neutral:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        confidence = max(overall_positive, overall_negative, overall_neutral)
        
        return {
            'sentiment': sentiment,
            'scores': {
                'positive': round(overall_positive, 3),
                'negative': round(overall_negative, 3),
                'neutral': round(overall_neutral, 3)
            },
            'confidence': round(confidence, 3)
        }
    
    def _generate_key_insights(
        self, 
        yahoo_data: Dict[str, Any],
        reddit_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []
        
        # Price movement insights
        if yahoo_data.get('success') and yahoo_data.get('stock_data'):
            stock_data = yahoo_data['stock_data']
            if stock_data.get('percent_change') != 'N/A':
                change = stock_data['percent_change']
                if '+' in change:
                    insights.append(f"Stock is up {change} from previous close")
                elif '-' in change:
                    insights.append(f"Stock is down {change.replace('-', '')} from previous close")
        
        # Social sentiment insights
        if reddit_data.get('success') and reddit_data.get('total_found', 0) > 0:
            insights.append(f"Found {reddit_data['total_found']} Reddit discussions")
        
        if twitter_data.get('success') and twitter_data.get('total_found', 0) > 0:
            insights.append(f"Analyzed {twitter_data['total_found']} tweets")
        
        # Sentiment insights
        sentiment_score = sentiment['sentiment']
        confidence = sentiment['confidence']
        
        if confidence > 0.6:
            insights.append(f"Strong {sentiment_score} sentiment detected (confidence: {confidence:.1%})")
        elif confidence > 0.4:
            insights.append(f"Moderate {sentiment_score} sentiment (confidence: {confidence:.1%})")
        else:
            insights.append(f"Mixed sentiment with low confidence ({confidence:.1%})")
        
        return insights
    
    def _generate_projections(
        self, 
        yahoo_data: Dict[str, Any],
        sentiment: Dict[str, Any],
        insights: List[str]
    ) -> Dict[str, str]:
        """Generate short-term and long-term projections."""
        
        sentiment_score = sentiment['sentiment']
        confidence = sentiment['confidence']
        
        # Short-term projection (1-7 days)
        if sentiment_score == 'positive' and confidence > 0.6:
            short_term = "Bullish outlook with potential upward momentum"
        elif sentiment_score == 'negative' and confidence > 0.6:
            short_term = "Bearish outlook with potential downward pressure"
        else:
            short_term = "Neutral outlook with sideways movement expected"
        
        # Long-term projection (1-3 months)
        if yahoo_data.get('success'):
            stock_data = yahoo_data.get('stock_data', {})
            # Simple heuristic based on available data
            if sentiment_score == 'positive':
                long_term = "Positive fundamentals suggest potential growth"
            elif sentiment_score == 'negative':
                long_term = "Negative sentiment may impact longer-term performance"
            else:
                long_term = "Mixed signals require further fundamental analysis"
        else:
            long_term = "Insufficient data for long-term projection"
        
        return {
            'short_term': short_term,
            'long_term': long_term
        }
    
    def _generate_executive_summary(
        self, 
        ticker: str,
        sentiment: Dict[str, Any],
        insights: List[str],
        projections: Dict[str, str]
    ) -> str:
        """Generate an executive summary of the analysis."""
        
        sentiment_desc = sentiment['sentiment'].upper()
        confidence = sentiment['confidence']
        
        summary = f"""
STOCK ANALYSIS SUMMARY FOR {ticker}

Overall Sentiment: {sentiment_desc} (Confidence: {confidence:.1%})

Key Findings:
{chr(10).join(f"• {insight}" for insight in insights[:5])}

Short-term Outlook: {projections['short_term']}

Long-term Outlook: {projections['long_term']}

Recommendation: Based on current sentiment analysis across news, social media, and market data, 
the stock shows {sentiment_desc.lower()} sentiment. Consider this analysis alongside fundamental 
and technical analysis for investment decisions.
        """.strip()
        
        return summary
    
    def _calculate_confidence_score(
        self, 
        yahoo_data: Dict[str, Any],
        reddit_data: Dict[str, Any],
        twitter_data: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence in the analysis."""
        
        confidence_factors = []
        
        # Data availability
        if yahoo_data.get('success'):
            confidence_factors.append(0.4)
        if reddit_data.get('success'):
            confidence_factors.append(0.3)
        if twitter_data.get('success'):
            confidence_factors.append(0.3)
        
        return sum(confidence_factors)
    
    def _assess_data_quality(
        self, 
        yahoo_data: Dict[str, Any],
        reddit_data: Dict[str, Any],
        twitter_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Assess the quality of data from each source."""
        
        quality = {}
        
        # Yahoo Finance data quality
        if yahoo_data.get('success'):
            headline_count = len(yahoo_data.get('headlines', []))
            if headline_count >= 5:
                quality['yahoo'] = 'high'
            elif headline_count >= 2:
                quality['yahoo'] = 'medium'
            else:
                quality['yahoo'] = 'low'
        else:
            quality['yahoo'] = 'failed'
        
        # Reddit data quality
        if reddit_data.get('success'):
            post_count = reddit_data.get('total_found', 0)
            if post_count >= 10:
                quality['reddit'] = 'high'
            elif post_count >= 3:
                quality['reddit'] = 'medium'
            else:
                quality['reddit'] = 'low'
        else:
            quality['reddit'] = 'failed'
        
        # Twitter data quality
        if twitter_data.get('success'):
            tweet_count = twitter_data.get('total_found', 0)
            if tweet_count >= 15:
                quality['twitter'] = 'high'
            elif tweet_count >= 5:
                quality['twitter'] = 'medium'
            else:
                quality['twitter'] = 'low'
        else:
            quality['twitter'] = 'failed'
        
        return quality
    
    def generate_ai_summary(
        self, 
        yahoo_data: Dict[str, Any], 
        reddit_data: Dict[str, Any], 
        twitter_data: Dict[str, Any], 
        ticker: str,
        sentiment_analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Generate AI-powered summary using Gemini API."""
        if not self.model:
            return None
            
        try:
            # Prepare data for AI analysis
            prompt = f"""
            Analyze stock sentiment data for {ticker} and provide a CONCISE summary (max 3-4 sentences).
            
            SENTIMENT: {sentiment_analysis.get('overall_sentiment', {}).get('sentiment', 'neutral')} 
            ({sentiment_analysis.get('overall_sentiment', {}).get('confidence', 0):.1f} confidence)
            
            SOURCES: {len(yahoo_data.get('headlines', []))} Yahoo headlines, {reddit_data.get('total_found', 0)} Reddit posts, {twitter_data.get('total_found', 0)} tweets
            
            KEY HEADLINES: {[h.get('title', '')[:80] + '...' if len(h.get('title', '')) > 80 else h.get('title', '') for h in yahoo_data.get('headlines', [])[:2]]}
            
            Provide a brief, professional summary covering: current sentiment, main drivers, and outlook. Keep it under 400 characters and avoid investment advice.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return None


if __name__ == "__main__":
    # Test the analyzer with mock data
    analyzer = AIStockAnalyzer()
    
    # Mock data for testing
    mock_yahoo = {
        'success': True,
        'headlines': [
            {'title': 'Apple reports strong earnings', 'summary': 'Revenue beat expectations'},
            {'title': 'AAPL stock upgraded by analysts', 'summary': 'Price target raised'}
        ]
    }
    
    mock_reddit = {
        'success': True,
        'posts': [
            {'title': 'AAPL to the moon!', 'text': 'Bullish on Apple', 'score': 100}
        ],
        'total_found': 1
    }
    
    mock_twitter = {
        'success': True,
        'tweets': [
            {'text': 'Buying more $AAPL today!', 'likes': 50, 'retweets': 10}
        ],
        'total_found': 1
    }
    
    result = analyzer.analyze_stock_sentiment(mock_yahoo, mock_reddit, mock_twitter, 'AAPL')
    
    if result['success']:
        print("✅ AI Analysis successful!")
        print(result['report']['summary'])
    else:
        print("❌ AI Analysis failed!")
        print(result['error'])
