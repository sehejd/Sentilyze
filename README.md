# Sentilyze - Multi-Source Market Sentiment & Fundamentals Engine

A personal-use, full-stack application that blends social sentiment, fundamentals,
political insider trading, geopolitical risk, and social/search momentum into a
single composite score per ticker - plus a rule-based backtesting panel to test
strategy ideas against real historical price data.

> Built for personal research use. The composite score, SWOT output, and
> backtest results are heuristic tools, not investment advice.

## What it does

- **ML sentiment** across Reddit, Twitter/X, and Yahoo Finance news headlines
  using a VADER + TextBlob ensemble (with an optional FinBERT transformer
  upgrade).
- **Fundamental analysis** combining live yfinance ratios with as-reported
  figures pulled straight from SEC EDGAR XBRL filings, scored 0-100 against
  configurable thresholds.
- **Quarterly/annual report tracking** via SEC EDGAR filing metadata (10-Q/10-K).
- **Political insider trading signal** from the public Senate & House Stock
  Watcher STOCK Act disclosure datasets.
- **Geopolitical exposure** via the GDELT Project's global news index, grouped
  by theme (trade policy, sanctions, conflict, elections/regulation, monetary
  policy, supply chain).
- **Social/search momentum**: Reddit mention velocity + Google Trends interest.
- **SWOT analysis** generated from all of the above (rule-based, optionally
  polished into prose by Gemini if you have an API key).
- **Composite "Sentilyze Score"**: a configurable weighted blend of every
  signal above, 0-100.
- **Political network "deeper dive"**: what bills a company lobbies for
  (Senate LDA filings), who sponsors those bills (Congress.gov), who the
  company's named executives are (SEC filing-sourced officer data), and what
  politicians those executives personally donate to (FEC). Cross-references
  bill sponsors against the ticker's congressional stock-trading disclosures
  and flags possible overlaps for manual verification. Loaded on demand from
  the main dashboard since it fans out to several slower public APIs.
- **Backtesting panel**: build entry/exit rules on technical indicators
  (SMA/EMA/RSI/MACD/Bollinger Bands/volume), add stop-loss/take-profit, and
  simulate against real historical daily price data, benchmarked vs buy & hold.
- **Political Web**: an interactive graph, not scoped to one ticker - the base
  layer plots the *entire* public STOCK Act dataset (every politician, every
  company they've disclosed trading), then layers in lobbying/bill-sponsor and
  executive-donation edges for the most active companies. Drag, zoom, click any
  node to see its connections. See `/political-web`.
- **Valuation calculator**: five independent fundamental valuation methods -
  Discounted Cash Flow, Comparable Company Analysis (sector peer multiples),
  Dividend Discount Model, Graham Number, and Asset-Based/Book Value - each
  with its own stated assumptions, plus a blended estimate. See `/valuation`.
- **Peer performance model**: a logistic regression comparing the company's
  fundamentals, news sentiment, and congressional trading signal against
  ~10-15 current sector peers, labeled by trailing price return, to surface
  which indicators correlate with outperformance in that peer set. This is a
  cross-sectional snapshot (free data doesn't expose historical point-in-time
  fundamentals), not a historical panel model - documented in depth below.

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in GEMINI_API_KEY (optional) and SEC_EDGAR_USER_AGENT
python app.py
```

The backend runs on `http://localhost:8000`.

SEC EDGAR requires a descriptive `User-Agent` with contact info on every
request (their policy, not ours) - set `SEC_EDGAR_USER_AGENT` in `.env`
before using the fundamentals/filings endpoints.

Optional: install `requirements-ml.txt` and set `USE_FINBERT=true` to swap the
default VADER+TextBlob sentiment ensemble for a transformer-based FinBERT
model (pulls in PyTorch, ~1GB+).

For the political "deeper dive" (lobbying + bills + campaign finance), set
`CONGRESS_GOV_API_KEY` (free signup) for bill titles/sponsors - without it,
lobbied bill numbers still surface but without enrichment. FEC campaign
finance lookups work out of the box against the public `DEMO_KEY`; set
`FEC_API_KEY` (also free) for a higher rate limit. The Senate LDA lobbying
API itself is public/keyless.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The main page runs the full multi-source
analysis; the nav bar's chart icon links to `/backtest`.

### Troubleshooting: "the site is static / nothing loads"

Both servers have to be running at once - `python app.py` (backend, port
8000) in one terminal and `npm run dev` (frontend, port 3000) in another.
If every panel looks empty/static and the political web graph never
appears, the frontend almost certainly can't reach the backend. Check, in
order:

1. **Is the backend actually still running?** `python app.py` should print
   `Running on http://0.0.0.0:8000` and stay running - if it printed a
   traceback and exited, that's the bug (paste the traceback).
2. **Browser DevTools → Network tab** while loading the page: do requests to
   `localhost:8000/api/...` appear at all?
   - No requests show up → a frontend JS error is likely preventing the
     fetch from firing at all; check the **Console** tab for a red error.
   - Requests show up but fail to connect (`ERR_CONNECTION_REFUSED`) → the
     backend isn't running or is on a different port.
   - Requests return **500** → the backend hit an error processing a real
     API response; check the backend terminal for a traceback.
   - Requests just hang / never resolve → likely a slow real upstream API
     (see below), not a bug - most panels load in a few seconds, but
     `/api/political-web` and `/api/peer-performance` fan out to several
     public APIs sequentially and can legitimately take 30s-2min depending
     on the caps you set.
3. **`NEXT_PUBLIC_API_URL`** - the frontend defaults to `http://localhost:8000`
   if unset, which matches the backend's default port. Only set this env var
   if you changed the backend's port.
4. As of this version, an unexpected error in one panel (e.g. a real API
   response shaped differently than expected) shows a visible "failed to
   render" message in that panel instead of silently blanking the page -
   if you still see a fully blank/static page with no error message
   anywhere, that's itself informative (check the Console tab).
5. **Yahoo Finance rate limiting** - fundamentals, valuation, comps, sector
   peers, company officers, backtesting, and the new price history chart all
   read from `yfinance`, which scrapes Yahoo's unofficial API. Yahoo
   aggressively rate-limits repeated requests (especially from cloud/hosting
   IPs), and if it trips, every one of those features degrades at once -
   this is the single most common cause of "the whole site is broken." All
   yfinance access now goes through `backend/utils/yf_client.py`, which
   caches successful responses (15 min) and retries rate-limited requests
   with exponential backoff before giving up. If a ticker still comes back
   empty after that, it's genuinely rate-limited at the moment - the failure
   is cached for only 90 seconds, so the *next* request for that ticker
   retries fresh instead of staying broken. If this happens constantly,
   Yahoo may be blocking your IP more aggressively than usual; waiting a
   few minutes and retrying is currently the only workaround.

## 🎯 Usage

1. Enter a ticker on the home page to see a real price history chart
   (with 20/50-day moving averages and a period selector), the composite
   score, fundamentals, insider trading, geopolitical exposure, social
   momentum, SWOT, and raw headlines/posts/tweets.
2. Go to `/backtest` to build a rule-based strategy - pick a preset (RSI
   mean reversion, SMA golden cross, MACD crossover, Bollinger bounce) or
   build your own rules from scratch (e.g. "buy when RSI < 30, sell when
   RSI > 70, 10% stop loss") - and run it over real historical price data.
3. Go to `/valuation` to run five independent valuation methods (DCF,
   comps, DDM, Graham number, asset-based), see a fair-value-by-method
   comparison chart against the current price, and optionally run the
   cross-sectional peer performance model.

## 🔧 API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/full-analysis?ticker=` | Everything combined: sentiment, fundamentals, insider, geopolitical, social trends, SWOT, composite score |
| `GET /api/composite?ticker=&w_*=` | Composite score only, with optional weight overrides |
| `GET /api/swot?ticker=` | SWOT analysis |
| `GET /api/fundamentals?ticker=` | Fundamental ratios + 0-100 score |
| `GET /api/sec/filings?ticker=` | Recent 10-Q/10-K filing metadata |
| `GET /api/insider?ticker=&days=` | Congressional (political) trading disclosures |
| `GET /api/geopolitical?ticker=` | Geopolitical news exposure by theme |
| `GET /api/social-trends?ticker=` | Reddit mention velocity + Google Trends interest |
| `GET /api/political-network?ticker=` | Deeper dive: lobbying, bills, sponsors, executives, campaign contributions, cross-referenced connections |
| `GET /api/political-web?days_back=&max_trading_edges=&max_lobbying_companies=&max_donation_companies=` | Multi-company politician↔company network graph |
| `GET /api/valuation?ticker=&peer_tickers=` | DCF, comps, DDM, Graham number, asset-based valuation + blended estimate |
| `GET /api/peer-performance?ticker=&lookback_months=&peer_tickers=` | Logistic regression vs. sector peers |
| `GET /api/price-history?ticker=&period=` | Real OHLCV + 20/50-day SMA for the dashboard price chart (`period`: `1mo`/`3mo`/`6mo`/`1y`/`2y`/`5y`, default `6mo`) |
| `GET /api/yahoo`, `/api/reddit`, `/api/twitter` | Individual raw source data |
| `GET /api/analyze?ticker=` | Legacy comprehensive endpoint (Yahoo/Reddit/Twitter only) |
| `GET /api/backtest/indicators` | Metadata for the backtest rule builder |
| `POST /api/backtest` | Run a rule-based backtest (see below) |
| `GET /health` | Health check |

### Backtest request shape

```json
{
  "ticker": "AAPL",
  "start": "2022-01-01",
  "end": "2024-01-01",
  "entry_rules": [{"field": "rsi_14", "operator": "<", "value": 30}],
  "exit_rules": [{"field": "rsi_14", "operator": ">", "value": 70}],
  "initial_capital": 10000,
  "position_size_pct": 1.0,
  "stop_loss_pct": 10,
  "take_profit_pct": 20,
  "fundamental_gate": {
    "enabled": true,
    "checks": [{"metric": "pe_ratio", "operator": "<", "value": 25}]
  }
}
```

## 🛠️ Architecture

### Backend (Python + Flask)
```
backend/
├── app.py                     # Flask routes
├── scraping/                  # Data source integrations
│   ├── yahoo.py, reddit.py, twitter.py   (original 3 sources)
│   ├── sec_edgar.py           # SEC EDGAR fundamentals & filings
│   ├── insider_trading.py     # Senate/House Stock Watcher
│   ├── geopolitical.py        # GDELT Project
│   ├── social_trends.py       # Reddit velocity + Google Trends
│   ├── lobbying.py            # Senate LDA lobbying disclosures + bill-reference extraction
│   ├── congress_bills.py      # Congress.gov bill/sponsor lookup
│   ├── company_officers.py    # Named executives (yfinance)
│   └── political_contributions.py  # FEC individual campaign contributions
├── analysis/
│   ├── ai_analyzer.py         # Original keyword-based analyzer + Gemini summary
│   ├── ml_sentiment.py        # VADER+TextBlob ensemble (optional FinBERT)
│   ├── fundamentals.py        # Fundamental scoring engine
│   ├── swot.py                # SWOT generator
│   ├── composite.py           # Weighted composite score
│   ├── orchestrator.py        # Fans out all sources in parallel, blends results
│   ├── political_network.py   # Per-ticker deeper-dive: lobbying + bills + executives + donations
│   ├── political_web.py       # Multi-company graph: full trading dataset + bounded lobbying/donation enrichment
│   ├── sector_peers.py        # Curated sector -> peer ticker lists (comps valuation + peer performance model)
│   ├── valuation.py           # DCF, comps, DDM, Graham number, asset-based valuation
│   ├── peer_performance_model.py  # Cross-sectional logistic regression vs. sector peers
│   └── price_history.py       # OHLCV + 20/50-day SMA for the dashboard price chart
├── backtesting/
│   ├── indicators.py          # SMA/EMA/RSI/MACD/Bollinger Bands
│   └── engine.py              # Rule-based backtest simulator
└── utils/
    ├── cache.py                # Disk cache for slow/rate-limited public datasets
    ├── yf_client.py             # Centralized cached/retrying yfinance access (see Troubleshooting above)
    └── political.py            # Shared name-matching helpers (political_network.py + political_web.py)
```

### Frontend (Next.js + TypeScript)
- **Components**: shadcn/ui + custom panels (`FundamentalsPanel`,
  `InsiderTradingPanel`, `GeopoliticalPanel`, `SocialTrendsPanel`, `SwotPanel`,
  `CompositeScoreGauge`, `PoliticalNetworkPanel`, `PriceHistoryChart`)
- **API Layer**: Axios-based client (`lib/api.ts`) with full TypeScript types
  for every endpoint
- **Backtesting UI**: `/backtest` - strategy presets + rule builder + equity
  curve chart (recharts)
- **Valuation UI**: `/valuation` - fair-value-by-method comparison chart +
  method explainer text + peer performance model (recharts)
  + trade log
- **Political Web UI**: `/political-web` - custom force-directed graph
  (`lib/graphLayout.ts`, `d3-force` for physics + plain SVG rendering),
  draggable/zoomable/pannable, click a node for its connections
- **Valuation UI**: `/valuation` - five valuation method cards with expandable
  assumptions, blended consensus, and a peer-performance section with a
  coefficient bar chart and sector peer table

## ⚠️ Known limitations (by design, given free data sources)

- **Backtest fundamental thresholds are a static gate, not point-in-time
  history.** Free data sources don't expose what a company's P/E ratio *was*
  on a given historical date - only current/as-currently-reported figures.
  A fundamental filter in the backtest panel is evaluated once against
  *today's* fundamentals, not re-evaluated per historical day. This is surfaced
  in the API response and UI copy so it isn't mistaken for real point-in-time
  backtesting.
- **Twitter/X data is mock** unless you configure a real Twitter API v2
  bearer token - X's API is no longer free for meaningful search volume.
- **Political insider trading covers congressional STOCK Act disclosures**
  (Senate + House), not corporate Form 4 executive trades.
- Google Trends (via `pytrends`) is an unofficial scraper and may rate-limit;
  the app degrades gracefully (returns an error field) rather than crashing.
- **Political network connections are heuristic name matches, not confirmed
  links.** Bill sponsor names (Congress.gov), congressional trader names
  (Stock Watcher), and donation recipient names (FEC) are formatted
  differently across these sources, so `political_network.py` matches on
  shared name tokens and flags results as "possible" - always verify manually
  before drawing conclusions.
- Bill titles/sponsors require a free `CONGRESS_GOV_API_KEY`; without it,
  bill numbers referenced in lobbying filings still surface, just unenriched.
- **The Political Web's "as many as possible" is bounded, and the bounds are
  returned in `caps_applied` rather than being a silent limit.** The base
  politician↔company trading layer genuinely covers the entire public STOCK
  Act dataset - that part isn't capped. Lobbying/bill-sponsor and executive-
  donation enrichment *is* capped (`max_lobbying_companies`,
  `max_donation_companies`) because those are real per-company/per-person
  calls against free public APIs (Senate LDA, Congress.gov, FEC); enriching
  every company in the trading dataset would take far too long and produce an
  unreadable graph. Raise the caps for a bigger graph at the cost of a slower
  build.
- **Valuation methods are assumption-driven, and the assumptions are the
  point.** DCF's fair value swings enormously with its growth/discount-rate
  inputs; Graham Number and DDM assume stable, mature businesses; Comps is
  only as good as the sector peer list. Every method's response includes its
  own assumptions - read them, don't just take the blended number.
- **The peer performance model is a cross-sectional snapshot, not a
  historical panel.** Free data sources (same limitation as the backtest
  engine) don't expose point-in-time historical fundamentals, so this can't
  train on "companies in this position historically" across many past
  periods. Instead it compares ~10-15 *current* sector peers' fundamentals
  against their own trailing price return. With that few observations,
  logistic regression coefficients are suggestive correlations within that
  specific snapshot, not statistically robust or forward-predictive findings
  - this is stated in every response's `methodology_caveat` field, not just
  here.

## 🎨 Color Scheme

- **Light**: `#fffcf2` - Page background, card backgrounds
- **Beige**: `#ccc5b9` - UI elements, borders
- **Gray**: `#403d39` - Text (main)
- **Dark**: `#252422` - Headers, bold text, containers
- **Red**: `#eb5e28` - Accent (negative sentiment)

## 📦 Tech Stack

### Frontend
- Next.js 15, TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, d3-force, Axios, Lucide React

### Backend
- Python 3.11+, Flask, yfinance, VADER + TextBlob (optional FinBERT via
  transformers/torch), scikit-learn, pandas, numpy, requests, pytrends,
  google-generativeai (optional)

## 🔮 Possible future enhancements

- [ ] Real Twitter/X API v2 integration
- [ ] Corporate Form 4 insider trading (SEC EDGAR full-text search)
- [ ] Historical sentiment/score tracking with a real database
- [ ] Point-in-time fundamentals via a paid data provider for true
      fundamentals-aware backtesting
- [ ] User authentication and saved watchlists/backtests
