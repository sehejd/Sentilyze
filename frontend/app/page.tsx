"use client"

import Link from "next/link"
import Navbar from "@/app/components/navbar"
import StockSummary from "@/app/components/StockSummary"
import HeadlineList from "@/app/components/HeadlineList"
import LoadingSpinner from "@/app/components/LoadingSpinner"
import CompositeScoreGauge from "@/app/components/CompositeScoreGauge"
import FundamentalsPanel from "@/app/components/FundamentalsPanel"
import SwotPanel from "@/app/components/SwotPanel"
import InsiderTradingPanel from "@/app/components/InsiderTradingPanel"
import GeopoliticalPanel from "@/app/components/GeopoliticalPanel"
import SocialTrendsPanel from "@/app/components/SocialTrendsPanel"
import PoliticalNetworkPanel from "@/app/components/PoliticalNetworkPanel"
import PriceHistoryChart from "@/app/components/PriceHistoryChart"
import ErrorBoundary from "@/app/components/ErrorBoundary"
import { ChevronDown, AlertCircle, LineChart } from "lucide-react"
import { useState } from "react"
import { StockData, SentimentAnalysisResponse, ComprehensiveAnalysisResponse, FullAnalysisResponse, ScraperSource } from "@/lib/api"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function Home() {
	const [searchResult, setSearchResult] = useState<StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | FullAnalysisResponse | null>(null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Handle search results from navbar
	const handleSearchResult = (data: StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | FullAnalysisResponse) => {
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

	// Check which shape of result we have
	const isFullAnalysis = searchResult && 'composite_score' in searchResult;
	const isComprehensiveAnalysis = searchResult && !isFullAnalysis && 'analysis' in searchResult;

	return (
		<div className="min-h-screen bg-light">
			<Navbar
				onSearchResult={handleSearchResult}
				onLoadingChange={handleLoadingChange}
				onError={handleError}
				defaultSource={ScraperSource.FULL}
			/>

			{/* Full Page Hero Section */}
			<div className="min-h-screen flex flex-col justify-center items-center relative px-6 overflow-hidden">
				{/* Depth: soft gradient glows + faint dot grid */}
				<div className="absolute -top-32 -right-32 w-[560px] h-[560px] glow-blob rounded-full" aria-hidden="true" />
				<div className="absolute -bottom-40 -left-24 w-[480px] h-[480px] glow-blob rounded-full opacity-70" aria-hidden="true" />
				<div
					className="absolute inset-0 dot-grid opacity-60"
					style={{ maskImage: "radial-gradient(ellipse at center, black, transparent 70%)", WebkitMaskImage: "radial-gradient(ellipse at center, black, transparent 70%)" }}
					aria-hidden="true"
				/>

				<div className="text-left mb-16 w-full max-w-6xl relative">
					<div className="inline-flex items-center gap-2 mb-6 px-3 py-1 rounded-full border border-beige bg-white/60 backdrop-blur-sm text-xs font-mono uppercase tracking-wider text-grayish">
						<span className="relative flex h-2 w-2">
							<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-red opacity-75" />
							<span className="relative inline-flex rounded-full h-2 w-2 bg-accent-red" />
						</span>
						Live multi-source analysis
					</div>
					<h1 className="text-8xl lg:text-9xl font-bold text-dark mb-8 tracking-tight">
						The real-time stock<br />
						<span className="bg-gradient-to-r from-dark to-accent-red bg-clip-text text-transparent">sentiment engine.</span>
					</h1>
					<p className="text-grayish max-w-lg font-mono text-lg mb-8">
						Sentiment, fundamentals, insider activity, geopolitics & social momentum, blended into one score
					</p>
					<Link
						href="/backtest"
						className="inline-flex items-center gap-2 text-sm font-mono text-dark border border-beige rounded-full px-4 py-2 bg-white/60 backdrop-blur-sm shadow-soft hover:shadow-soft-lg hover:-translate-y-0.5 hover:border-accent-red/40 transition-all"
					>
						<LineChart className="w-4 h-4" />
						Try the backtesting panel
					</Link>
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
								<Alert className="border-accent-red bg-red-50">
									<AlertCircle className="h-4 w-4 text-accent-red" />
									<AlertDescription className="text-dark">
										{error}
									</AlertDescription>
								</Alert>
							</div>
						)}

						{/* Full Analysis Results (fundamentals, insider, geopolitical, social, SWOT, composite score) */}
						{isFullAnalysis && !isLoading && (
							<div className="w-full max-w-6xl mx-auto space-y-4">
								<div className="flex items-center gap-4 flex-wrap p-5 rounded-xl border border-beige bg-gradient-to-br from-white to-light shadow-soft">
						<div className="flex items-center justify-center w-14 h-14 rounded-xl bg-dark text-white font-bold text-lg shrink-0 shadow-soft">
							{searchResult.ticker.slice(0, 4)}
						</div>
						<div className="flex-1 min-w-0">
							<h2 className="text-2xl font-bold text-dark truncate">
								{searchResult.company_name} <span className="text-grayish font-medium">(${searchResult.ticker})</span>
							</h2>
							<div className="flex items-center gap-2 mt-1">
								<span
									className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
										searchResult.sentiment.blended.overall_label === "positive"
											? "bg-green-100 text-green-700"
											: searchResult.sentiment.blended.overall_label === "negative"
											? "bg-red-100 text-accent-red"
											: "bg-beige/60 text-grayish"
									}`}
								>
									<span className={`w-1.5 h-1.5 rounded-full ${
										searchResult.sentiment.blended.overall_label === "positive"
											? "bg-green-500"
											: searchResult.sentiment.blended.overall_label === "negative"
											? "bg-accent-red"
											: "bg-grayish"
									}`} />
									<span className="capitalize">{searchResult.sentiment.blended.overall_label}</span> sentiment
								</span>
								<span className="text-xs text-grayish">
									{searchResult.sentiment.blended.n_sources} source{searchResult.sentiment.blended.n_sources === 1 ? '' : 's'}
								</span>
							</div>
						</div>
					</div>

								<ErrorBoundary label="Price history">
									<PriceHistoryChart ticker={searchResult.ticker} />
								</ErrorBoundary>

								<ErrorBoundary label="Composite score">
									<CompositeScoreGauge composite={searchResult.composite_score} />
								</ErrorBoundary>

								<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
									<ErrorBoundary label="Fundamentals"><FundamentalsPanel fundamentals={searchResult.fundamentals} /></ErrorBoundary>
									<ErrorBoundary label="Insider trading"><InsiderTradingPanel insider={searchResult.insider_trading} /></ErrorBoundary>
									<ErrorBoundary label="Geopolitical"><GeopoliticalPanel geopolitical={searchResult.geopolitical} /></ErrorBoundary>
									<ErrorBoundary label="Social trends"><SocialTrendsPanel social={searchResult.social_trends} /></ErrorBoundary>
								</div>

								<ErrorBoundary label="SWOT analysis">
									<SwotPanel swot={searchResult.swot} />
								</ErrorBoundary>

								<ErrorBoundary label="Political network deeper dive">
									<PoliticalNetworkPanel ticker={searchResult.ticker} companyName={searchResult.company_name} />
								</ErrorBoundary>

								<ErrorBoundary label="Headlines">
									<HeadlineList
										rawData={searchResult.raw_data}
										ticker={searchResult.ticker}
									/>
								</ErrorBoundary>
							</div>
						)}

						{/* Comprehensive Analysis Results (legacy /api/analyze) */}
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
						{searchResult && !isComprehensiveAnalysis && !isFullAnalysis && !isLoading && (
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
													searchResult.change.toString().startsWith('-') ? 'text-accent-red' : 'text-grayish'
												}`}>
													{searchResult.change}
												</p>
											</div>
											<div>
												<p className="text-grayish">Percent Change</p>
												<p className={`text-xl font-semibold ${
													searchResult.percent_change.toString().startsWith('+') ? 'text-green-500' : 
													searchResult.percent_change.toString().startsWith('-') ? 'text-accent-red' : 'text-grayish'
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
															headline.sentiment === 'negative' ? 'bg-accent-red text-white' :
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