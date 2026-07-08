# analysis/swot.py - SWOT analysis generator
"""
Builds a Strengths/Weaknesses/Opportunities/Threats breakdown from the other
analysis modules' output: fundamentals scoring, blended sentiment, political
insider trading signal, geopolitical exposure, and social momentum.

Strengths/Weaknesses = internal, fundamentals-driven.
Opportunities/Threats = external, driven by sentiment/momentum/politics/geopolitics.

The structured bullet lists are always rule-based and deterministic (no LLM
required). If GEMINI_API_KEY is configured, we additionally ask Gemini to
turn the structured bullets into a short prose narrative - purely cosmetic,
the structured data is unaffected if that call fails or is unavailable.
"""

import os
from typing import Dict, Any, List, Optional


def _fundamentals_bullets(fundamentals: Dict[str, Any]) -> Dict[str, List[str]]:
    strengths, weaknesses = [], []
    if not fundamentals or not fundamentals.get('success'):
        return {'strengths': strengths, 'weaknesses': weaknesses}

    scoring = fundamentals.get('scoring', {})
    metrics = fundamentals.get('metrics', {})

    metric_labels = {
        'pe_ratio': 'P/E ratio', 'peg_ratio': 'PEG ratio', 'price_to_book': 'Price/Book',
        'debt_to_equity': 'Debt/Equity', 'current_ratio': 'Current ratio',
        'return_on_equity': 'Return on equity', 'profit_margin': 'Profit margin',
        'revenue_growth': 'Revenue growth', 'earnings_growth': 'Earnings growth',
    }

    for item in scoring.get('breakdown', []):
        if item['score'] is None:
            continue
        label = metric_labels.get(item['metric'], item['metric'])
        if item['score'] >= 75:
            strengths.append(f"{label} of {item['value']} is in a healthy range")
        elif item['score'] <= 25:
            weaknesses.append(f"{label} of {item['value']} is weak relative to typical thresholds")

    overall = scoring.get('overall_score')
    if overall is not None:
        if overall >= 75:
            strengths.append(f"Overall fundamental score of {overall}/100 ({scoring.get('rating')})")
        elif overall < 45:
            weaknesses.append(f"Overall fundamental score of {overall}/100 ({scoring.get('rating')}) trails healthy benchmarks")

    beta = metrics.get('beta')
    if beta is not None and beta > 1.5:
        weaknesses.append(f"High beta ({beta}) implies above-market volatility")

    debt = metrics.get('total_debt')
    cash = metrics.get('total_cash')
    if debt is not None and cash is not None and cash > 0:
        if debt > cash * 3:
            weaknesses.append("Total debt significantly exceeds cash reserves")
        elif cash > debt:
            strengths.append("Cash reserves exceed total debt")

    return {'strengths': strengths, 'weaknesses': weaknesses}


def _sentiment_bullets(sentiment_summary: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    opportunities, threats = [], []
    if not sentiment_summary:
        return {'opportunities': opportunities, 'threats': threats}

    label = sentiment_summary.get('overall_label') or sentiment_summary.get('sentiment')
    compound = sentiment_summary.get('overall_compound', sentiment_summary.get('confidence', 0))

    if label == 'positive':
        opportunities.append(f"Blended social/news sentiment is positive (score {compound})")
    elif label == 'negative':
        threats.append(f"Blended social/news sentiment is negative (score {compound})")

    return {'opportunities': opportunities, 'threats': threats}


def _insider_bullets(insider: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    opportunities, threats = [], []
    if not insider or not insider.get('success'):
        return {'opportunities': opportunities, 'threats': threats}

    agg = insider.get('aggregate', {})
    signal = agg.get('signal_label')
    members = agg.get('unique_members', 0)

    if signal == 'net_buying':
        opportunities.append(f"Net congressional buying activity detected across {members} member(s) - a bullish 'smart money' signal")
    elif signal == 'net_selling':
        threats.append(f"Net congressional selling activity detected across {members} member(s) - a bearish 'smart money' signal")

    return {'opportunities': opportunities, 'threats': threats}


def _geopolitical_bullets(geo: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    threats = []
    if not geo or not geo.get('success'):
        return {'threats': threats}

    exposure = geo.get('geopolitical_exposure')
    themes = geo.get('themes', {})

    if exposure in ('moderate', 'high'):
        theme_names = ', '.join(t.replace('_', ' ') for t in themes.keys())
        threats.append(f"{exposure.capitalize()} geopolitical news exposure ({theme_names}) over the last month")

    return {'threats': threats}


def _social_trends_bullets(social: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    opportunities, threats = [], []
    if not social:
        return {'opportunities': opportunities, 'threats': threats}

    momentum = (social.get('reddit_momentum') or {}).get('momentum')
    if momentum == 'surging':
        opportunities.append("Reddit mention volume is surging - elevated retail interest may drive short-term volatility/momentum")
        threats.append("Rapid retail-driven mention spikes can reverse quickly, creating downside crowd-momentum risk")
    elif momentum == 'rising':
        opportunities.append("Reddit mention volume is trending up, indicating growing retail attention")
    elif momentum == 'fading':
        threats.append("Retail social media interest is fading, which can reduce short-term liquidity/momentum")

    trend_direction = (social.get('search_interest') or {}).get('trend_direction')
    if trend_direction == 'rising':
        opportunities.append("Google search interest for the company is trending upward")

    return {'opportunities': opportunities, 'threats': threats}


def _try_ai_narrative(ticker: str, swot: Dict[str, List[str]]) -> Optional[str]:
    """Best-effort Gemini narrative polish; returns None if unavailable or it fails."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""
        Turn this structured SWOT analysis for {ticker} into a concise narrative (max 5 sentences, no investment advice, no headers).

        Strengths: {swot['strengths']}
        Weaknesses: {swot['weaknesses']}
        Opportunities: {swot['opportunities']}
        Threats: {swot['threats']}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None


def generate_swot(
    ticker: str,
    fundamentals: Optional[Dict[str, Any]] = None,
    sentiment_summary: Optional[Dict[str, Any]] = None,
    insider: Optional[Dict[str, Any]] = None,
    geopolitical: Optional[Dict[str, Any]] = None,
    social_trends: Optional[Dict[str, Any]] = None,
    include_ai_narrative: bool = True,
) -> Dict[str, Any]:
    """Assemble a full SWOT analysis from already-fetched analysis module outputs."""
    fund = _fundamentals_bullets(fundamentals)
    sent = _sentiment_bullets(sentiment_summary)
    ins = _insider_bullets(insider)
    geo = _geopolitical_bullets(geopolitical)
    soc = _social_trends_bullets(social_trends)

    swot = {
        'strengths': fund['strengths'] or ["No standout fundamental strengths identified from available data"],
        'weaknesses': fund['weaknesses'] or ["No major fundamental weaknesses identified from available data"],
        'opportunities': (sent['opportunities'] + ins['opportunities'] + soc['opportunities']) or
                          ["No significant external tailwinds identified from available data"],
        'threats': (sent['threats'] + ins['threats'] + geo['threats'] + soc['threats']) or
                   ["No significant external risks identified from available data"],
    }

    result = {
        'ticker': ticker.upper().strip(),
        'swot': swot,
        'ai_narrative': None,
    }

    if include_ai_narrative:
        result['ai_narrative'] = _try_ai_narrative(ticker, swot)

    return result


if __name__ == "__main__":
    mock_fundamentals = {
        'success': True,
        'scoring': {
            'overall_score': 82.0, 'rating': 'good',
            'breakdown': [{'metric': 'pe_ratio', 'value': 18, 'score': 75}],
        },
        'metrics': {'beta': 1.2, 'total_debt': 1000, 'total_cash': 5000},
    }
    print(generate_swot("AAPL", fundamentals=mock_fundamentals, include_ai_narrative=False))
