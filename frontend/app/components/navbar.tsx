import { Input } from "@/components/ui/input"
import { Search, Home, User, Loader2, LineChart } from "lucide-react"
import { useState, KeyboardEvent, useEffect } from "react"
import Link from "next/link"
import { useSearch } from "@/lib/hooks/useSearch"
import { ScraperSource, StockData, SentimentAnalysisResponse, ComprehensiveAnalysisResponse, FullAnalysisResponse } from "@/lib/api"

type SearchResultData = StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | FullAnalysisResponse;

interface NavbarProps {
  onSearchResult?: (data: SearchResultData) => void;
  onLoadingChange?: (loading: boolean) => void;
  onError?: (error: string) => void;
  defaultSource?: ScraperSource;
}

export default function Navbar({ 
  onSearchResult, 
  onLoadingChange,
  onError,
  defaultSource = ScraperSource.YAHOO 
}: NavbarProps) {
  const [ticker, setTicker] = useState("");
  const { isLoading, error, data, searchTicker, clearResults } = useSearch();

  // Handle search submission
  const handleSearch = async () => {
    if (!ticker.trim()) return;
    
    try {
      await searchTicker(ticker, defaultSource);
    } catch (err) {
      if (onError) {
        onError(err instanceof Error ? err.message : 'Search failed');
      }
    }
  };

  // Watch for loading state changes
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(isLoading);
    }
  }, [isLoading, onLoadingChange]);

  // Watch for error changes
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Watch for data changes and call the callback
  useEffect(() => {
    if (data && onSearchResult) {
      onSearchResult(data);
    }
  }, [data, onSearchResult]);

  // Handle Enter key press
  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setTicker(value);
    
    // Clear previous results when user starts typing
    if (data || error) {
      clearResults();
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Nav Header with Icons */}
          <div className="flex items-center space-x-8">
            <h1 className="text-xl font-semibold text-gray-900" style={{ fontFamily: 'Limelight' }}>
              SENTILYZE
            </h1>
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Home className="w-4 h-4 text-gray-600 hover:text-gray-900 cursor-pointer transition-colors" />
              </Link>
              <Link href="/backtest" title="Backtesting">
                <LineChart className="w-4 h-4 text-gray-600 hover:text-gray-900 cursor-pointer transition-colors" />
              </Link>
              <User className="w-4 h-4 text-gray-600 hover:text-gray-900 cursor-pointer transition-colors" />
            </div>
          </div>

          {/* Search Input */}
          <div className="flex-shrink-0 relative">
            <div className="relative w-64">
              <Input
                type="text"
                placeholder="Search ticker..."
                value={ticker}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                className="pr-10 bg-white/70 border-gray-200/50 focus:bg-white focus:border-gray-300"
                disabled={isLoading}
              />
              <button
                onClick={handleSearch}
                disabled={isLoading || !ticker.trim()}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
            
            {/* Error display */}
            {error && (
              <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-red-50 border border-red-200 rounded-md text-sm text-red-600 z-50">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
