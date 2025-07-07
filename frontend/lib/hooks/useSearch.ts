import { useState, useCallback } from 'react';
import { 
  fetchFromScraper, 
  ScraperSource, 
  StockData, 
  SentimentAnalysisResponse,
  ComprehensiveAnalysisResponse,
  isValidTicker 
} from '@/lib/api';

interface UseSearchResult {
  isLoading: boolean;
  error: string | null;
  data: StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | null;
  searchTicker: (ticker: string, source?: ScraperSource) => Promise<void>;
  clearResults: () => void;
}

export const useSearch = (): UseSearchResult => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | null>(null);

  const searchTicker = useCallback(async (
    ticker: string, 
    source: ScraperSource = ScraperSource.YAHOO
  ) => {
    // Validate ticker
    if (!ticker.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }

    if (!isValidTicker(ticker)) {
      setError('Please enter a valid ticker symbol (1-5 letters)');
      return;
    }

    setIsLoading(true);
    setError(null);
    setData(null);

    try {
      const result = await fetchFromScraper(ticker, source);
      
      if (result) {
        setData(result);
      } else {
        setError(`No data found for ticker ${ticker.toUpperCase()}`);
      }
    } catch (err) {
      const errorMessage = `Failed to fetch data for ${ticker.toUpperCase()}. Please try again.`;
      setError(errorMessage);
      console.error('Search error:', err);
      throw new Error(errorMessage); // Re-throw for external error handling
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    isLoading,
    error,
    data,
    searchTicker,
    clearResults
  };
};
