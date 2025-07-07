🧠 Copilot Instructions: Stock Sentiment Analyzer
📝 Overview
Build a full-stack app that lets users type in a stock ticker (e.g., TSLA) and instantly see real-time sentiment analysis from Yahoo Finance and Reddit headlines. The frontend visualizes sentiment trends with colored tags and a time-series graph.

🎨 Color Scheme
Use the following color palette, going from lightest to darkest neutrals, with red as the accent:

Name	Hex	Usage
Light	#fffcf2	Page background, card backgrounds
Beige	#ccc5b9	UI elements, borders
Gray	#403d39	Text (main)
Dark	#252422	Headers, bold text, containers
Red	#eb5e28	Accent (negative sentiment)

📦 Tech Stack
Frontend: Next.js + shadcn/ui + TailwindCSS (with custom colors)

Middleware: Axiom (for request logging and async processing)

Backend: Python (for scraping and NLP sentiment analysis)

🚧 User Flow
User types in a stock ticker (e.g., TSLA) into an input field.

Frontend sends request to the backend via Axiom middleware.

Backend:

Scrapes latest headlines from Yahoo Finance & Reddit.

Applies sentiment analysis (via TextBlob / VADER / HuggingFace).

Returns headlines with sentiment scores and timestamps.

Frontend:

Displays each headline with a color-coded tag:

🟢 Positive — green-500

🟡 Neutral — yellow-400

🔴 Negative — #eb5e28 (custom)

Renders a line chart showing sentiment trend over time.

Optional: Allow toggling between news sources.

💻 Frontend Tasks (Next.js + shadcn/ui)
 Add custom Tailwind color palette:

js
Copy
Edit
// tailwind.config.js
theme: {
  extend: {
    colors: {
      light: '#fffcf2',
      beige: '#ccc5b9',
      grayish: '#403d39',
      dark: '#252422',
      accent: '#eb5e28',
    },
  },
}
 Input field for ticker search.

 Button to trigger analysis.

 Table or list showing scraped headlines + sentiment tag.

 Tags:

Use bg-green-500, bg-yellow-400, and bg-[#eb5e28] for sentiments.

 Chart (e.g., using recharts) showing sentiment over time.

 Loading & error states using shadcn/ui Alerts or Skeletons.

 Light/Dark mode toggle (optional) leveraging dark variants of Tailwind.

🌐 Middleware (Axiom)
 Relay request to Python backend.

 Log request data and handle retries/failures gracefully.

 Store trace ID for frontend reference/debug.

🐍 Backend Tasks (Python)
 Endpoint: /analyze?ticker=TSLA

 Scrape latest headlines from:

Yahoo Finance (yfinance, requests, BeautifulSoup)

Reddit (via praw or pushshift.io / scraping)

 Apply sentiment analysis with:

Option A: TextBlob (simple)

Option B: VADER (financial domain-tuned)

Option C: transformers (distilbert-base-uncased-finetuned-sst-2-english)

 Return JSON format:

json
Copy
Edit
{
  "ticker": "TSLA",
  "headlines": [
    {
      "text": "Tesla reports record earnings",
      "sentiment": "positive",
      "timestamp": "2025-07-07T12:00:00Z",
      "source": "Yahoo Finance"
    }
  ]
}
✅ Optional Features
 Toggle between Yahoo / Reddit / Both

 Historical sentiment (store in DB)

 Keyword-based filtering

 Export data (CSV / JSON)

 Authentication (save searches)