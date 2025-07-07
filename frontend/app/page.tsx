"use client"

import Navbar from "@/app/components/navbar"
import StockSummary from "@/app/components/StockSummary"
import HeadlineList from "@/app/components/HeadlineList"
import LoadingSpinner from "@/app/components/LoadingSpinner"
import { ChevronDown, AlertCircle } from "lucide-react"
import { useState } from "react"
import { StockData, SentimentAnalysisResponse, ComprehensiveAnalysisResponse, ScraperSource } from "@/lib/api"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function Home() {
	const [searchResult, setSearchResult] = useState<StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | null>(null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Handle search results from navbar
	const handleSearchResult = (data: StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse) => {
		setSearchResult(data);
		setError(null);
		// Scroll to results section
		const resultsSection = document.getElementById('results-section');
		if (resultsSection) {
			resultsSection.scrollIntoView({ behavior: 'smooth' });
		}
	};

	// Handle loading state
	const handleLoadingChange = (loading: boolean) => {
		setIsLoading(loading);
		if (loading) {
			setError(null);
			// Scroll to results section when loading starts
			const resultsSection = document.getElementById('results-section');
			if (resultsSection) {
				resultsSection.scrollIntoView({ behavior: 'smooth' });
			}
		}
	};

	// Handle error state
	const handleError = (errorMessage: string) => {
		setError(errorMessage);
		setIsLoading(false);
		// Scroll to results section to show error
		const resultsSection = document.getElementById('results-section');
		if (resultsSection) {
			resultsSection.scrollIntoView({ behavior: 'smooth' });
		}
	};

	// Check if we have comprehensive analysis data
	const isComprehensiveAnalysis = searchResult && 'analysis' in searchResult;

	return (
		<div className="min-h-screen bg-light">
			<Navbar 
				onSearchResult={handleSearchResult} 
				onLoadingChange={handleLoadingChange}
				onError={handleError}
				defaultSource={ScraperSource.ALL} 
			/>
			
			{/* Full Page Hero Section */}
			<div className="min-h-screen flex flex-col justify-center items-center relative px-6">
				<div className="text-left mb-16 w-full max-w-6xl">
					<h1 className="text-8xl lg:text-9xl font-bold text-dark mb-8 tracking-tight">
						The real-time stock<br />
						sentiment engine.
					</h1>
					<p className="text-grayish max-w-lg font-mono text-lg mb-16">
						Real-time market sentiment from news & social media powered by AI
					</p>
				</div>
				
				{/* Scroll indicator */}
				<div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex flex-col items-center animate-bounce">
					<span className="text-xs font-mono uppercase tracking-wider text-grayish mb-2">
						{(searchResult || isLoading || error) ? 'View Results' : 'Search to Get Started'}
					</span>
					<ChevronDown className="w-6 h-6 text-grayish" />
				</div>
			</div>

			{/* Results Section */}
			{(searchResult || isLoading || error) && (
				<div id="results-section" className="bg-white px-6 py-12">
					<div className="max-w-7xl mx-auto">
						
						{/* Loading State */}
						{isLoading && <LoadingSpinner />}

						{/* Error State */}
						{error && !isLoading && (
							<div className="w-full max-w-4xl mx-auto">
								<Alert className="border-accent bg-red-50">
									<AlertCircle className="h-4 w-4 text-accent" />
									<AlertDescription className="text-dark">
										{error}
									</AlertDescription>
								</Alert>
							</div>
						)}

						{/* Comprehensive Analysis Results */}
						{isComprehensiveAnalysis && !isLoading && (
							<div className="space-y-6">
								<StockSummary 
									ticker={searchResult.ticker} 
									analysis={searchResult.analysis} 
								/>
								<HeadlineList 
									rawData={searchResult.raw_data} 
									ticker={searchResult.ticker} 
								/>
							</div>
						)}

						{/* Legacy Simple Results (fallback) */}
						{searchResult && !isComprehensiveAnalysis && !isLoading && (
							<div className="w-full max-w-4xl mx-auto">
								{/* Stock Data Display */}
								{'current_price' in searchResult && (
									<div className="bg-light rounded-lg p-6 border border-beige mb-8">
										<h3 className="text-2xl font-semibold mb-4 text-dark">
											{searchResult.stock_name} ({searchResult.ticker})
										</h3>
										<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
											<div>
												<p className="text-grayish">Current Price</p>
												<p className="text-2xl font-bold text-dark">${searchResult.current_price}</p>
											</div>
											<div>
												<p className="text-grayish">Change</p>
												<p className={`text-xl font-semibold ${
													searchResult.change.toString().startsWith('+') ? 'text-green-500' : 
													searchResult.change.toString().startsWith('-') ? 'text-accent' : 'text-grayish'
												}`}>
													{searchResult.change}
												</p>
											</div>
											<div>
												<p className="text-grayish">Percent Change</p>
												<p className={`text-xl font-semibold ${
													searchResult.percent_change.toString().startsWith('+') ? 'text-green-500' : 
													searchResult.percent_change.toString().startsWith('-') ? 'text-accent' : 'text-grayish'
												}`}>
													{searchResult.percent_change}
												</p>
											</div>
										</div>
									</div>
								)}

								{/* Simple Sentiment Data Display */}
								{'headlines' in searchResult && (
									<div className="bg-light rounded-lg p-6 border border-beige">
										<h3 className="text-2xl font-semibold mb-4 text-dark">
											Sentiment Analysis for {searchResult.ticker}
										</h3>
										<div className="space-y-4">
											{searchResult.headlines.map((headline, index) => (
												<div key={index} className="border-b border-beige pb-4 last:border-b-0">
													<div className="flex items-start justify-between gap-4">
														<div className="flex-1">
															<p className="text-dark mb-2">{headline.text}</p>
															<div className="flex items-center gap-2 text-sm text-grayish">
																<span>{headline.source}</span>
																<span>•</span>
																<span>{new Date(headline.timestamp).toLocaleDateString()}</span>
															</div>
														</div>
														<div className={`px-3 py-1 rounded-full text-sm font-medium ${
															headline.sentiment === 'positive' ? 'bg-green-500 text-white' :
															headline.sentiment === 'negative' ? 'bg-accent text-white' :
															'bg-yellow-400 text-white'
														}`}>
															{headline.sentiment}
														</div>
													</div>
												</div>
											))}
										</div>
									</div>
								)}
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	)
}