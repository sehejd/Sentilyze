# Sentilyze

## Overview
Sentilyze is a financial forecasting app that analyzes the sentiment of stocks based on news headlines scraped from Yahoo Finance and Reddit. The app uses sentiment analysis tools like TextBlob, VADER, or HuggingFace transformers to provide insights into stock performance.

## Real-World Use Case
1. A user types in a stock ticker symbol, e.g., TSLA.
2. The app scrapes news headlines from Yahoo Finance and Reddit.
3. Each headline is passed through sentiment analysis.
4. Results are returned:
   - "Tesla stock downgraded by analysts" → negative
   - "Tesla reports record earnings" → positive
5. The frontend displays these results with colors and a graph showing:
   - 📉 Sentiment dips before earnings call
   - 📈 Rises after good news
6. The user can decide to do more research or adjust their portfolio.

## Tech Stack
- **Frontend**: Next.js + shadcn/ui
- **Middleground**: Axios
- **Backend**: Python

## Directory Structure
- `frontend/`: Contains the Next.js frontend.
- `backend/`: Contains the Python backend.

## Features
- Scrapes news from Yahoo Finance and Reddit.
- Performs sentiment analysis on headlines.
- Displays sentiment trends with graphs and color-coded results.

## Installation
1. Navigate to the `frontend` directory and set up the Next.js app.
2. Navigate to the `backend` directory and set up the Python backend.
3. Ensure Axios is configured to connect the frontend and backend.

## Usage
1. Start the backend server.
2. Start the frontend server.
3. Open the app in your browser and type in a stock ticker symbol to analyze sentiment.
