import axios from 'axios';

// Define the base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Define types for our API responses
export interface StockData {
  ticker: string;
  stock_name: string;
  current_price: number | string;
  change: string;
  percent_change: string;
}

export interface HeadlineData {
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  timestamp: string;
  source: string;
}

export interface SentimentAnalysisResponse {
  ticker: string;
  headlines: HeadlineData[];
}

// Comprehensive analysis response type
export interface ComprehensiveAnalysisResponse {
  ticker: string;
  analysis: {
    overall_sentiment?: {
      sentiment: string;
      confidence: number;
      positive: number;
      negative: number;
      neutral: number;
    };
    ai_summary?: string;
    summary?: string;
    analysis_timestamp?: string;
    confidence_score?: number;
    source_analysis?: any;
    key_insights?: any;
    projections?: any;
    data_quality?: any;
  };
  raw_data: {
    yahoo_finance?: {
      success: boolean;
      headlines?: Array<{
        title: string;
        summary?: string;
        url?: string;
        timestamp?: string;
        source?: string;
      }>;
      total_found?: number;
    };
    reddit?: {
      success: boolean;
      posts?: Array<{
        title: string;
        text?: string;
        url?: string;
        score?: number;
        created_utc?: number;
        subreddit?: string;
        author?: string;
      }>;
      total_found?: number;
    };
    twitter?: {
      success: boolean;
      tweets?: Array<{
        text: string;
        likes?: number;
        retweets?: number;
        timestamp?: string;
        username?: string;
      }>;
      total_found?: number;
    };
  };
  timestamp: string;
  api_version: string;
}

// Enum for different scraper sources
export enum ScraperSource {
  YAHOO = 'yahoo',
  REDDIT = 'reddit',
  TWITTER = 'twitter',
  ALL = 'analyze' // Changed to use the comprehensive analysis endpoint
}

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generic function to fetch data from any scraper
export const fetchFromScraper = async (
  ticker: string, 
  source: ScraperSource = ScraperSource.YAHOO
): Promise<StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | null> => {
  try {
    const endpoint = getEndpointForSource(source);
    const response = await apiClient.get(`${endpoint}?ticker=${ticker.toUpperCase()}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching data from ${source} for ticker ${ticker}:`, error);
    throw error; // Re-throw the error so it can be handled by the caller
  }
};

// Helper function to get the correct endpoint for each source
const getEndpointForSource = (source: ScraperSource): string => {
  switch (source) {
    case ScraperSource.YAHOO:
      return '/api/yahoo';
    case ScraperSource.REDDIT:
      return '/api/reddit';
    case ScraperSource.TWITTER:
      return '/api/twitter';
    case ScraperSource.ALL:
      return '/api/analyze';
    default:
      return '/api/yahoo';
  }
};

// Specific functions for each scraper (for convenience)
export const fetchYahooData = (ticker: string): Promise<StockData | null> => 
  fetchFromScraper(ticker, ScraperSource.YAHOO) as Promise<StockData | null>;

export const fetchRedditSentiment = (ticker: string): Promise<SentimentAnalysisResponse | null> => 
  fetchFromScraper(ticker, ScraperSource.REDDIT) as Promise<SentimentAnalysisResponse | null>;

export const fetchTwitterSentiment = (ticker: string): Promise<SentimentAnalysisResponse | null> => 
  fetchFromScraper(ticker, ScraperSource.TWITTER) as Promise<SentimentAnalysisResponse | null>;

export const fetchAllSentiment = (ticker: string): Promise<ComprehensiveAnalysisResponse | null> => 
  fetchFromScraper(ticker, ScraperSource.ALL) as Promise<ComprehensiveAnalysisResponse | null>;

// Function to validate ticker format
export const isValidTicker = (ticker: string): boolean => {
  return /^[A-Z]{1,5}$/.test(ticker.toUpperCase());
};
