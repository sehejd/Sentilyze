# analysis/composite.py - Composite "Sentilyze Score" engine
"""
Combines every signal the app gathers into one weighted 0-100 score:

  - sentiment        blended ML sentiment across Reddit/Twitter/news (ml_sentiment.py)
  - fundamentals      fundamental analysis score (fundamentals.py)
  - insider           net congressional buy/sell signal (insider_trading.py)
  - geopolitical       inverse of geopolitical risk exposure (geopolitical.py)
  - social_momentum   retail/search attention momentum (social_trends.py)

This is a transparent, configurable heuristic aggregator, not a trained
model - the weights are opinionated defaults meant to be tuned by the user
for personal use, not a claim of predictive accuracy. It is not investment
advice.
"""

from typing import Dict, Any, Optional

DEFAULT_WEIGHTS = {
    'sentiment': 0.30,
    'fundamentals': 0.30,
    'insider': 0.15,
    'geopolitical': 0.10,
    'social_momentum': 0.15,
}

_MOMENTUM_SCORES = {'surging': 85.0, 'rising': 70.0, 'steady': 50.0, 'fading': 30.0}
_EXPOSURE_RISK_SCORES = {'low': 100.0, 'moderate': 60.0, 'high': 20.0}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def normalize_weights(weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    """Merge user overrides with defaults and renormalize to sum to 1.0."""
    merged = dict(DEFAULT_WEIGHTS)
    if weights:
        for key, value in weights.items():
            if key in merged and value is not None:
                try:
                    merged[key] = max(0.0, float(value))
                except (TypeError, ValueError):
                    continue

    total = sum(merged.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in merged.items()}


def compute_composite_score(
    sentiment_compound: Optional[float] = None,
    fundamentals_score: Optional[float] = None,
    insider_signal: Optional[float] = None,
    geopolitical_exposure: Optional[str] = None,
    social_momentum: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute the weighted composite score. Any component may be None if that
    data source failed/was unavailable - its weight is redistributed across
    the remaining available components.
    """
    normalized_weights = normalize_weights(weights)

    components: Dict[str, Optional[float]] = {
        'sentiment': _clamp((sentiment_compound + 1) / 2 * 100) if sentiment_compound is not None else None,
        'fundamentals': _clamp(fundamentals_score) if fundamentals_score is not None else None,
        'insider': _clamp((insider_signal + 1) / 2 * 100) if insider_signal is not None else None,
        'geopolitical': _EXPOSURE_RISK_SCORES.get(geopolitical_exposure) if geopolitical_exposure else None,
        'social_momentum': _MOMENTUM_SCORES.get(social_momentum) if social_momentum else None,
    }

    available_weight = sum(normalized_weights[k] for k, v in components.items() if v is not None)

    if available_weight == 0:
        return {
            'score': None,
            'rating': 'insufficient_data',
            'components': components,
            'weights_used': normalized_weights,
        }

    weighted_sum = sum(
        components[k] * (normalized_weights[k] / available_weight)
        for k in components if components[k] is not None
    )
    score = round(weighted_sum, 1)

    if score >= 75:
        rating = 'strongly_bullish'
    elif score >= 60:
        rating = 'bullish'
    elif score >= 40:
        rating = 'neutral'
    elif score >= 25:
        rating = 'bearish'
    else:
        rating = 'strongly_bearish'

    return {
        'score': score,
        'rating': rating,
        'components': components,
        'weights_used': normalized_weights,
        'disclaimer': 'A heuristic composite of the signals below, not investment advice.',
    }


if __name__ == "__main__":
    result = compute_composite_score(
        sentiment_compound=0.4,
        fundamentals_score=82.0,
        insider_signal=0.5,
        geopolitical_exposure='low',
        social_momentum='rising',
    )
    print(result)
