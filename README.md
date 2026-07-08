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
- **Backtesting panel**: build entry/exit rules on technical indicators
  (SMA/EMA/RSI/MACD/Bollinger Bands/volume), add stop-loss/take-profit, and
  simulate against real historical daily price data, benchmarked vs buy & hold.

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

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The main page runs the full multi-source
analysis; the nav bar's chart icon links to `/backtest`.

## 🎯 Usage

1. Enter a ticker on the home page to see the composite score, fundamentals,
   insider trading, geopolitical exposure, social momentum, SWOT, and raw
   headlines/posts/tweets.
2. Go to `/backtest` to build a rule-based strategy (e.g. "buy when RSI < 30,
   sell when RSI > 70, 10% stop loss") and run it over real historical price
   data.

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
│   └── social_trends.py       # Reddit velocity + Google Trends
├── analysis/
│   ├── ai_analyzer.py         # Original keyword-based analyzer + Gemini summary
│   ├── ml_sentiment.py        # VADER+TextBlob ensemble (optional FinBERT)
│   ├── fundamentals.py        # Fundamental scoring engine
│   ├── swot.py                # SWOT generator
│   ├── composite.py           # Weighted composite score
│   └── orchestrator.py        # Fans out all sources in parallel, blends results
├── backtesting/
│   ├── indicators.py          # SMA/EMA/RSI/MACD/Bollinger Bands
│   └── engine.py              # Rule-based backtest simulator
└── utils/cache.py             # Disk cache for slow/rate-limited public datasets
```

### Frontend (Next.js + TypeScript)
- **Components**: shadcn/ui + custom panels (`FundamentalsPanel`,
  `InsiderTradingPanel`, `GeopoliticalPanel`, `SocialTrendsPanel`, `SwotPanel`,
  `CompositeScoreGauge`)
- **API Layer**: Axios-based client (`lib/api.ts`) with full TypeScript types
  for every endpoint
- **Backtesting UI**: `/backtest` - rule builder + equity curve chart (recharts)
  + trade log

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

## 🎨 Color Scheme

- **Light**: `#fffcf2` - Page background, card backgrounds
- **Beige**: `#ccc5b9` - UI elements, borders
- **Gray**: `#403d39` - Text (main)
- **Dark**: `#252422` - Headers, bold text, containers
- **Red**: `#eb5e28` - Accent (negative sentiment)

## 📦 Tech Stack

### Frontend
- Next.js 15, TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, Axios, Lucide React

### Backend
- Python 3.11+, Flask, yfinance, VADER + TextBlob (optional FinBERT via
  transformers/torch), pandas, requests, pytrends, google-generativeai (optional)

## 🔮 Possible future enhancements

- [ ] Real Twitter/X API v2 integration
- [ ] Corporate Form 4 insider trading (SEC EDGAR full-text search)
- [ ] Historical sentiment/score tracking with a real database
- [ ] Point-in-time fundamentals via a paid data provider for true
      fundamentals-aware backtesting
- [ ] User authentication and saved watchlists/backtests
