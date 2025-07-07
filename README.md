# Sentilyze - Stock Sentiment Analyzer

A full-stack application that provides real-time sentiment analysis for stock tickers using data from Yahoo Finance, Reddit, and Twitter.

## 🚀 Quick Start

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the setup script (Windows):
   ```bash
   run.bat
   ```

   Or manually:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

3. The backend will be running on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser

## 🎯 Usage

1. Enter a stock ticker (e.g., AAPL, TSLA, GOOGL) in the search bar
2. Press Enter or click the search button
3. View the stock data and sentiment analysis results

## 🔧 API Endpoints

- `GET /api/yahoo?ticker=AAPL` - Get stock data from Yahoo Finance
- `GET /api/reddit?ticker=AAPL` - Get sentiment from Reddit (placeholder)
- `GET /api/twitter?ticker=AAPL` - Get sentiment from Twitter (placeholder)
- `GET /api/analyze?ticker=AAPL` - Get comprehensive analysis (placeholder)
- `GET /health` - Health check

## 🛠️ Architecture

### Frontend (Next.js + TypeScript)
- **Components**: Reusable UI components using shadcn/ui
- **API Layer**: Axios-based API client with TypeScript interfaces
- **Custom Hooks**: `useSearch` hook for managing search state
- **Styling**: Tailwind CSS with custom color palette

### Backend (Python + Flask)
- **API**: RESTful endpoints for different data sources
- **Scrapers**: Modular scraping system for Yahoo Finance, Reddit, Twitter
- **CORS**: Enabled for cross-origin requests from frontend

## 🎨 Color Scheme

- **Light**: `#fffcf2` - Page background, card backgrounds
- **Beige**: `#ccc5b9` - UI elements, borders
- **Gray**: `#403d39` - Text (main)
- **Dark**: `#252422` - Headers, bold text, containers
- **Red**: `#eb5e28` - Accent (negative sentiment)

## 📦 Tech Stack

### Frontend
- Next.js 15
- TypeScript
- Tailwind CSS 4
- shadcn/ui components
- Axios for HTTP requests
- Lucide React for icons

### Backend
- Python 3.8+
- Flask web framework
- yfinance for Yahoo Finance data
- Flask-CORS for cross-origin requests

## 🔮 Future Enhancements

- [ ] Implement Reddit scraping with PRAW
- [ ] Add Twitter/X API integration
- [ ] Sentiment analysis with TextBlob/VADER/HuggingFace
- [ ] Historical sentiment tracking
- [ ] Chart visualization with time-series data
- [ ] User authentication and saved searches
- [ ] Database integration for historical data
- [ ] Real-time updates with WebSockets


