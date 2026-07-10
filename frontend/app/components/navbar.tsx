import { Input } from "@/components/ui/input"
import { Search, Home, User, Loader2, LineChart, Network, Calculator } from "lucide-react"
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

  const navLinks = [
    { href: "/", icon: Home, title: "Home" },
    { href: "/backtest", icon: LineChart, title: "Backtesting" },
    { href: "/political-web", icon: Network, title: "Political Web" },
    { href: "/valuation", icon: Calculator, title: "Valuation Calculator" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-[0_1px_12px_-4px_rgba(0,0,0,0.08)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Nav Header with Icons */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="font-limelight text-xl tracking-wide text-dark hover:text-accent-red transition-colors">
              SENTILYZE
            </Link>
            <div className="flex items-center space-x-1">
              {navLinks.map(({ href, icon: Icon, title }) => (
                <Link
                  key={href}
                  href={href}
                  title={title}
                  className="p-2 rounded-lg text-gray-500 hover:text-accent-red hover:bg-accent-red/10 cursor-pointer transition-colors"
                >
                  <Icon className="w-4 h-4" />
                </Link>
              ))}
              <span className="p-2 rounded-lg text-gray-500 hover:text-accent-red hover:bg-accent-red/10 cursor-pointer transition-colors">
                <User className="w-4 h-4" />
              </span>
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
                className="pr-10 bg-white/70 border-gray-200/50 focus:bg-white focus:border-gray-300 focus:shadow-[0_0_0_3px_rgba(235,94,40,0.12)] transition-shadow"
                disabled={isLoading}
              />
              <button
                onClick={handleSearch}
                disabled={isLoading || !ticker.trim()}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 hover:text-accent-red disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
              <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-red-50 border border-red-200 rounded-md text-sm text-red-600 z-50 shadow-lg">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
