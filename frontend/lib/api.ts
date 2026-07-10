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
    source_analysis?: Record<string, unknown>;
    key_insights?: unknown;
    projections?: unknown;
    data_quality?: Record<string, unknown>;
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

// ---- New: fundamentals, insider trading, geopolitical, social trends, SWOT, composite score, backtesting ----

export interface FundamentalMetrics {
  pe_ratio: number | null;
  forward_pe: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  return_on_equity: number | null;
  return_on_assets: number | null;
  profit_margin: number | null;
  operating_margin: number | null;
  gross_margin: number | null;
  revenue_growth: number | null;
  earnings_growth: number | null;
  dividend_yield: number | null;
  beta: number | null;
  market_cap: number | null;
  free_cash_flow: number | null;
  total_cash: number | null;
  total_debt: number | null;
}

export interface FundamentalScoreBreakdown {
  metric: string;
  value: number | null;
  score: number | null;
  weight: number;
}

export interface FundamentalsResponse {
  success: boolean;
  ticker: string;
  company_name: string;
  sector?: string;
  industry?: string;
  metrics: FundamentalMetrics;
  as_reported_sec_data?: Record<string, { latest_value: number; latest_period_end: string; latest_form: string }> | null;
  scoring?: {
    overall_score: number | null;
    rating: 'strong' | 'good' | 'fair' | 'weak' | 'insufficient_data';
    breakdown: FundamentalScoreBreakdown[];
    data_coverage: string;
  };
  source: string;
  error?: string;
}

export interface SecFiling {
  form: string;
  filing_date: string | null;
  report_period: string | null;
  accession_number: string;
  document_url: string;
  filing_index_url: string;
}

export interface SecFilingsResponse {
  success: boolean;
  ticker: string;
  cik: string;
  company_name: string;
  sic_description?: string;
  filings: SecFiling[];
  error?: string;
}

export interface CongressionalTransaction {
  chamber: 'Senate' | 'House';
  member: string;
  ticker: string;
  transaction_type: string;
  transaction_date: string;
  amount_range: string;
  amount: { low: number; high: number };
  asset_description: string;
}

export interface InsiderTradingResponse {
  success: boolean;
  ticker: string;
  transactions: CongressionalTransaction[];
  total_found: number;
  lookback_days: number;
  aggregate: {
    buy_dollars_mid_estimate: number;
    sell_dollars_mid_estimate: number;
    net_signal: number;
    signal_label: 'net_buying' | 'net_selling' | 'mixed' | 'no_activity';
    unique_members: number;
  };
  source: string;
  error?: string;
}

export interface GeopoliticalArticle {
  title: string;
  url: string;
  source: string;
  published: string;
  language: string;
}

export interface GeopoliticalResponse {
  success: boolean;
  ticker: string;
  subject_searched: string;
  themes: Record<string, GeopoliticalArticle[]>;
  total_articles: number;
  geopolitical_exposure: 'low' | 'moderate' | 'high';
  partial_errors: string[];
  source: string;
  error?: string;
}

export interface SocialTrendsResponse {
  ticker: string;
  reddit_momentum: {
    success: boolean;
    mentions_today?: number;
    mentions_trailing_week?: number;
    trailing_week_daily_avg?: number;
    velocity_ratio?: number;
    momentum?: 'surging' | 'rising' | 'steady' | 'fading';
    error?: string;
  };
  search_interest: {
    success: boolean;
    query_term?: string;
    series?: Array<{ date: string; interest: number }>;
    recent_week_avg_interest?: number;
    trend_direction?: 'rising' | 'falling' | 'flat' | 'unknown';
    note?: string;
    error?: string;
  };
  timestamp: string;
}

export interface SwotResponse {
  ticker: string;
  swot: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  ai_narrative: string | null;
}

export interface CompositeScoreData {
  score: number | null;
  rating: 'strongly_bullish' | 'bullish' | 'neutral' | 'bearish' | 'strongly_bearish' | 'insufficient_data';
  components: {
    sentiment: number | null;
    fundamentals: number | null;
    insider: number | null;
    geopolitical: number | null;
    social_momentum: number | null;
  };
  weights_used: Record<string, number>;
  disclaimer?: string;
}

export interface CompositeScoreResponse {
  ticker: string;
  composite_score: CompositeScoreData;
  sentiment: { overall_label: string; overall_compound: number; n_sources: number };
  timestamp: string;
}

export interface FullAnalysisResponse {
  ticker: string;
  company_name: string;
  raw_data: ComprehensiveAnalysisResponse['raw_data'];
  fundamentals: FundamentalsResponse;
  insider_trading: InsiderTradingResponse;
  geopolitical: GeopoliticalResponse;
  social_trends: SocialTrendsResponse;
  sentiment: {
    by_source: Record<string, { overall_label: string; overall_compound: number; n: number }>;
    blended: { overall_label: string; overall_compound: number; n_sources: number };
  };
  swot: SwotResponse;
  composite_score: CompositeScoreData;
  weights_used: Record<string, number>;
  timestamp: string;
  api_version: string;
}

export interface CompositeWeightOverrides {
  sentiment?: number;
  fundamentals?: number;
  insider?: number;
  geopolitical?: number;
  social_momentum?: number;
}

// ---- Backtesting ----

export interface BacktestRule {
  field: string;
  operator: '<' | '<=' | '>' | '>=' | '==' | 'crosses_above' | 'crosses_below';
  value: number | string;
}

export interface FundamentalGateCheck {
  metric: string;
  operator: '<' | '<=' | '>' | '>=' | '==';
  value: number;
}

export interface BacktestRequest {
  ticker: string;
  start: string;
  end?: string;
  entry_rules: BacktestRule[];
  exit_rules: BacktestRule[];
  initial_capital?: number;
  position_size_pct?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  fundamental_gate?: {
    enabled: boolean;
    checks: FundamentalGateCheck[];
  };
}

export interface BacktestTrade {
  action: 'buy' | 'sell';
  date: string;
  price: number;
  shares: number;
  cost?: number;
  proceeds?: number;
  reason?: string;
  return_pct?: number;
  entry_date?: string;
  entry_price?: number;
}

export interface BacktestResponse {
  success: boolean;
  ticker: string;
  period: { start: string; end: string; requested_start: string; requested_end?: string };
  entry_gate: { passed: boolean; note: string | null };
  initial_capital: number;
  final_equity: number;
  stats: {
    total_return_pct: number;
    cagr_pct: number;
    max_drawdown_pct: number;
    sharpe_ratio: number | null;
    num_trades: number;
    win_rate_pct: number | null;
    buy_hold_return_pct: number;
    alpha_vs_buy_hold_pct: number;
  };
  trades: BacktestTrade[];
  equity_curve: Array<{ date: string; equity: number; close: number }>;
  buy_hold_equity_curve: Array<{ date: string; equity: number }>;
  fundamental_gate_limitation: string;
  error?: string;
}

export interface BacktestIndicatorsResponse {
  indicators: Record<string, { label: string; unit: string; range?: [number, number] }>;
  operators: string[];
  fundamental_metrics: Record<string, { direction: 'low' | 'high'; bands: [number, number, number] }>;
}

// ---- Political "deeper dive": lobbying, bills, executives, campaign finance ----

export interface LobbyingFilingSummary {
  filing_uuid: string;
  registrant: string | null;
  filing_year: number;
  filing_period: string;
  amount: number | null;
  bill_references: string[];
  dt_posted: string;
}

export interface LobbyingBillReference {
  bill_type: string;
  number: string;
  raw: string;
  mentions: number;
  issue_areas: string[];
}

export interface LobbyingSummary {
  success: boolean;
  ticker?: string;
  company_name?: string;
  total_filings: number;
  estimated_total_spend: number;
  registrants: string[];
  issue_areas: Record<string, number>;
  bill_references: LobbyingBillReference[];
  filings: LobbyingFilingSummary[];
  source: string;
  error?: string;
}

export interface BillSponsor {
  name: string;
  party: string | null;
  state: string | null;
  bioguide_id: string | null;
  chamber: 'House' | 'Senate';
}

export interface PoliticalBill {
  success: boolean;
  congress?: number;
  bill_type: string;
  bill_number: string;
  title?: string;
  sponsor?: BillSponsor | null;
  cosponsors_count?: number;
  policy_area?: string;
  introduced_date?: string;
  latest_action?: { text: string; date: string };
  congress_gov_url?: string;
  mentions?: number;
  issue_areas?: string[];
  error?: string;
  source: string;
}

export interface CompanyOfficer {
  name: string;
  title: string | null;
  age: number | null;
  total_pay: number | null;
  year_born: number | null;
}

export interface OfficersResult {
  success: boolean;
  ticker?: string;
  company_name?: string;
  officers: CompanyOfficer[];
  note?: string;
  error?: string;
  source?: string;
}

export interface PoliticalDonation {
  contributor_name: string;
  contributor_employer: string | null;
  contributor_occupation: string | null;
  amount: number;
  date: string;
  committee_name: string | null;
  committee_party: string | null;
  candidate_name: string | null;
  election_year: number | null;
}

export interface ExecutiveDonationEntry {
  name: string;
  title: string | null;
  donations: PoliticalDonation[];
  lookup_error?: string | null;
}

export interface ExecutiveDonationsResult {
  success: boolean;
  employer_searched: string;
  executives: ExecutiveDonationEntry[];
  source: string;
  timestamp: string;
}

export interface PoliticalConnection {
  type: 'bill_sponsor_trades_stock' | 'executive_donated_to_bill_sponsor';
  description: string;
  bill: string;
  sponsor?: string;
  trader_name?: string;
  executive?: string;
  donation_amount?: number;
  donation_date?: string;
  confidence: string;
}

export interface PoliticalNetworkResponse {
  ticker: string;
  company_name: string;
  lobbying: LobbyingSummary;
  bills: PoliticalBill[];
  officers: OfficersResult;
  executive_donations: ExecutiveDonationsResult | null;
  connections: PoliticalConnection[];
  congress_gov_configured: boolean;
  timestamp: string;
  disclaimer: string;
}

// ---- Multi-company political web graph ----

export type PoliticalWebNodeType = 'politician' | 'company' | 'bill' | 'executive';
export type PoliticalWebEdgeType = 'trades' | 'lobbies_for' | 'sponsored_by' | 'works_at' | 'donated_to';

export interface PoliticalWebNode {
  id: string;
  type: PoliticalWebNodeType;
  label: string;
  chamber?: string;
  party?: string;
  state?: string;
  ticker?: string;
  title?: string;
  url?: string;
}

export interface PoliticalWebEdge {
  source: string;
  target: string;
  type: PoliticalWebEdgeType;
  weight: number;
  direction?: 'net_buying' | 'net_selling' | 'mixed';
  last_date?: string;
  amount?: number;
  date?: string;
}

export interface PoliticalWebResponse {
  success: boolean;
  nodes: PoliticalWebNode[];
  edges: PoliticalWebEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    node_counts: Record<string, number>;
    dataset_totals: { total_transactions: number; unique_members: number; unique_tickers: number };
    total_disclosed_trading_pairs: number;
  };
  caps_applied: Record<string, number>;
  congress_gov_configured: boolean;
  timestamp: string;
  disclaimer: string;
  error?: string;
}

export interface PoliticalWebParams {
  days_back?: number;
  max_trading_edges?: number;
  max_lobbying_companies?: number;
  max_donation_companies?: number;
}

// ---- Valuation calculator ----

export type ValuationMethodType = 'dcf' | 'comparable_company_analysis' | 'ddm' | 'graham_number' | 'asset_based';

export interface ValuationMethodResult {
  method: ValuationMethodType;
  applicable: boolean;
  fair_value_per_share?: number;
  current_price?: number;
  upside_pct?: number;
  assumptions?: Record<string, unknown>;
  note: string;
  peers_used?: string[];
}

export interface ValuationResponse {
  success: boolean;
  ticker: string;
  company_name: string;
  sector?: string;
  industry?: string;
  current_price: number;
  methods: ValuationMethodResult[];
  methods_applicable: number;
  blended_fair_value_per_share: number | null;
  blended_upside_pct: number | null;
  rating: 'undervalued' | 'overvalued' | 'fairly_valued' | 'insufficient_data';
  timestamp: string;
  disclaimer: string;
  error?: string;
}

// ---- Peer performance logistic regression ----

export interface PeerPerformanceCoefficient {
  feature: string;
  label: string;
  coefficient: number;
  direction: string;
}

export interface PeerTableRow {
  ticker: string;
  company_name: string;
  trailing_return_pct: number;
  outperformed_median: boolean;
}

export interface PeerPerformanceResponse {
  success: boolean;
  ticker: string;
  sector?: string;
  lookback_months: number;
  peer_count: number;
  sector_median_return_pct: number;
  target: {
    trailing_return_pct: number | null;
    outperformed_median: boolean | null;
    predicted_probability_of_outperformance: number;
    features: Record<string, number | null>;
  };
  model: {
    type: string;
    trained_on: string;
    regularization_C: number;
    coefficients: PeerPerformanceCoefficient[];
    train_accuracy: number;
  };
  peer_table: PeerTableRow[];
  timestamp: string;
  methodology_caveat: string;
  error?: string;
}

// Enum for different scraper sources
export enum ScraperSource {
  YAHOO = 'yahoo',
  REDDIT = 'reddit',
  TWITTER = 'twitter',
  ALL = 'analyze', // Legacy comprehensive analysis endpoint (Yahoo/Reddit/Twitter only)
  FULL = 'full-analysis' // Full dashboard: adds fundamentals, insider, geopolitical, social trends, SWOT, composite score
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
): Promise<StockData | SentimentAnalysisResponse | ComprehensiveAnalysisResponse | FullAnalysisResponse | null> => {
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
    case ScraperSource.FULL:
      return '/api/full-analysis';
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

export const fetchFullAnalysis = (ticker: string): Promise<FullAnalysisResponse | null> =>
  fetchFromScraper(ticker, ScraperSource.FULL) as Promise<FullAnalysisResponse | null>;

// Function to validate ticker format
export const isValidTicker = (ticker: string): boolean => {
  return /^[A-Z]{1,5}$/.test(ticker.toUpperCase());
};

// ---- New dedicated endpoint fetchers ----

export const fetchFundamentals = async (ticker: string): Promise<FundamentalsResponse> => {
  const response = await apiClient.get(`/api/fundamentals?ticker=${ticker.toUpperCase()}`);
  return response.data;
};

export const fetchSecFilings = async (ticker: string): Promise<SecFilingsResponse> => {
  const response = await apiClient.get(`/api/sec/filings?ticker=${ticker.toUpperCase()}`);
  return response.data;
};

export const fetchInsiderTrading = async (ticker: string, days = 365): Promise<InsiderTradingResponse> => {
  const response = await apiClient.get(`/api/insider?ticker=${ticker.toUpperCase()}&days=${days}`);
  return response.data;
};

export const fetchGeopolitical = async (ticker: string): Promise<GeopoliticalResponse> => {
  const response = await apiClient.get(`/api/geopolitical?ticker=${ticker.toUpperCase()}`);
  return response.data;
};

export const fetchSocialTrends = async (ticker: string): Promise<SocialTrendsResponse> => {
  const response = await apiClient.get(`/api/social-trends?ticker=${ticker.toUpperCase()}`);
  return response.data;
};

export const fetchSwot = async (ticker: string): Promise<SwotResponse> => {
  const response = await apiClient.get(`/api/swot?ticker=${ticker.toUpperCase()}`);
  return response.data;
};

export const fetchCompositeScore = async (
  ticker: string,
  weights?: CompositeWeightOverrides
): Promise<CompositeScoreResponse> => {
  const params = new URLSearchParams({ ticker: ticker.toUpperCase() });
  if (weights) {
    if (weights.sentiment !== undefined) params.set('w_sentiment', String(weights.sentiment));
    if (weights.fundamentals !== undefined) params.set('w_fundamentals', String(weights.fundamentals));
    if (weights.insider !== undefined) params.set('w_insider', String(weights.insider));
    if (weights.geopolitical !== undefined) params.set('w_geopolitical', String(weights.geopolitical));
    if (weights.social_momentum !== undefined) params.set('w_social_momentum', String(weights.social_momentum));
  }
  const response = await apiClient.get(`/api/composite?${params.toString()}`);
  return response.data;
};

export const fetchBacktestIndicators = async (): Promise<BacktestIndicatorsResponse> => {
  const response = await apiClient.get('/api/backtest/indicators');
  return response.data;
};

export const runBacktest = async (request: BacktestRequest): Promise<BacktestResponse> => {
  const response = await apiClient.post('/api/backtest', request);
  return response.data;
};

export const fetchPoliticalNetwork = async (
  ticker: string,
  companyName?: string
): Promise<PoliticalNetworkResponse> => {
  const params = new URLSearchParams({ ticker: ticker.toUpperCase() });
  if (companyName) params.set('company_name', companyName);
  const response = await apiClient.get(`/api/political-network?${params.toString()}`);
  return response.data;
};

export const fetchPoliticalWeb = async (params: PoliticalWebParams = {}): Promise<PoliticalWebResponse> => {
  const query = new URLSearchParams();
  if (params.days_back !== undefined) query.set('days_back', String(params.days_back));
  if (params.max_trading_edges !== undefined) query.set('max_trading_edges', String(params.max_trading_edges));
  if (params.max_lobbying_companies !== undefined) query.set('max_lobbying_companies', String(params.max_lobbying_companies));
  if (params.max_donation_companies !== undefined) query.set('max_donation_companies', String(params.max_donation_companies));
  const response = await apiClient.get(`/api/political-web?${query.toString()}`, { timeout: 120000 });
  return response.data;
};

export const fetchValuation = async (ticker: string, peerTickers?: string[]): Promise<ValuationResponse> => {
  const params = new URLSearchParams({ ticker: ticker.toUpperCase() });
  if (peerTickers && peerTickers.length > 0) params.set('peer_tickers', peerTickers.join(','));
  const response = await apiClient.get(`/api/valuation?${params.toString()}`, { timeout: 60000 });
  return response.data;
};

export const fetchPeerPerformance = async (
  ticker: string,
  lookbackMonths = 12,
  peerTickers?: string[]
): Promise<PeerPerformanceResponse> => {
  const params = new URLSearchParams({ ticker: ticker.toUpperCase(), lookback_months: String(lookbackMonths) });
  if (peerTickers && peerTickers.length > 0) params.set('peer_tickers', peerTickers.join(','));
  const response = await apiClient.get(`/api/peer-performance?${params.toString()}`, { timeout: 90000 });
  return response.data;
};

// ---- Price history ----

export interface PricePoint {
  date: string;
  close: number;
  volume: number | null;
  sma_20: number | null;
  sma_50: number | null;
}

export type PriceHistoryPeriod = '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y';

export interface PriceHistoryResponse {
  success: boolean;
  ticker: string;
  period: string;
  points: PricePoint[];
  period_return_pct: number;
  period_high: number | null;
  period_low: number | null;
  timestamp: string;
  source: string;
  error?: string;
}

export const fetchPriceHistory = async (
  ticker: string,
  period: PriceHistoryPeriod = '6mo'
): Promise<PriceHistoryResponse> => {
  const params = new URLSearchParams({ ticker: ticker.toUpperCase(), period });
  const response = await apiClient.get(`/api/price-history?${params.toString()}`, { timeout: 45000 });
  return response.data;
};
