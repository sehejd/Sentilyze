# analysis/ml_sentiment.py - ML-based sentiment engine
"""
Replaces naive keyword counting with real sentiment models:

- Default: an ensemble of VADER (a lexicon + rule-based model tuned for
  short, informal social-media text - it knows slang like "to the moon",
  emoji, and intensifiers) and TextBlob's pattern-analyzer sentiment model.
  Both run locally, no API key, fast enough for interactive use.

- Optional: ProsusAI/FinBERT, a BERT model fine-tuned specifically on
  financial text, loaded via HuggingFace `transformers` when
  USE_FINBERT=true and the (heavy) ML extras are installed. This is a real
  transformer-based classifier, not a bag-of-words model - it substantially
  outperforms the default ensemble on financial-domain phrasing, at the cost
  of a ~400MB model download and slower inference.

Every public function returns the same shape regardless of which backend is
active, so callers don't need to know which model produced a score.
"""

import os
from typing import Dict, List, Any
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

_vader = SentimentIntensityAnalyzer()

# Financial-domain slang VADER doesn't know out of the box
_FINANCE_LEXICON_BOOST = {
    'bullish': 2.5, 'bearish': -2.5, 'moon': 2.0, 'mooning': 2.5, 'rocket': 2.0,
    'squeeze': 1.5, 'diamond hands': 2.0, 'hodl': 1.5, 'to the moon': 2.5,
    'paper hands': -1.5, 'bag holder': -2.0, 'bagholder': -2.0, 'bagholders': -2.0, 'rekt': -2.5,
    'dump': -2.0, 'dumping': -2.0, 'pump': 1.5, 'pumping': 1.5,
    'short squeeze': 2.0, 'buy the dip': 1.5, 'dead cat bounce': -1.5,
    'overvalued': -1.5, 'undervalued': 1.5, 'earnings beat': 2.0, 'earnings miss': -2.0,
    'guidance raise': 2.0, 'guidance cut': -2.0, 'downgrade': -1.5, 'upgrade': 1.5,
}
_vader.lexicon.update(_FINANCE_LEXICON_BOOST)


def _use_finbert() -> bool:
    return os.getenv('USE_FINBERT', 'false').lower() == 'true'


@lru_cache(maxsize=1)
def _get_finbert_pipeline():
    """Lazily load FinBERT only if explicitly enabled - avoids forcing the
    ~400MB torch/transformers install on users who just want the default
    ensemble."""
    from transformers import pipeline  # heavy optional dependency
    return pipeline('sentiment-analysis', model='ProsusAI/finbert')


def classify_text(text: str) -> Dict[str, Any]:
    """
    Score a single piece of text. Returns a normalized result:
    {compound: -1..1, positive: 0..1, negative: 0..1, neutral: 0..1, label: str, model: str}
    """
    text = (text or '').strip()
    if not text:
        return {'compound': 0.0, 'positive': 0.0, 'negative': 0.0, 'neutral': 1.0,
                'label': 'neutral', 'model': 'none'}

    if _use_finbert():
        try:
            result = _get_finbert_pipeline()(text[:512])[0]
            label = result['label'].lower()
            score = result['score']
            compound = score if label == 'positive' else -score if label == 'negative' else 0.0
            return {
                'compound': round(compound, 4),
                'positive': round(score, 4) if label == 'positive' else 0.0,
                'negative': round(score, 4) if label == 'negative' else 0.0,
                'neutral': round(score, 4) if label == 'neutral' else round(1 - score, 4),
                'label': label,
                'model': 'finbert',
            }
        except Exception:
            pass  # fall through to the default ensemble if FinBERT fails at runtime

    vader_scores = _vader.polarity_scores(text)
    try:
        textblob_polarity = TextBlob(text).sentiment.polarity
    except Exception:
        textblob_polarity = 0.0

    # Ensemble: weight VADER higher (it's tuned for informal/social text)
    compound = round(0.65 * vader_scores['compound'] + 0.35 * textblob_polarity, 4)

    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'

    return {
        'compound': compound,
        'positive': round(vader_scores['pos'], 4),
        'negative': round(vader_scores['neg'], 4),
        'neutral': round(vader_scores['neu'], 4),
        'label': label,
        'model': 'vader+textblob_ensemble',
    }


def classify_batch(texts: List[str], weights: List[float] = None) -> Dict[str, Any]:
    """
    Score a list of texts and aggregate into an overall distribution.
    `weights` (e.g. Reddit upvotes, tweet engagement) let popular posts count
    more toward the aggregate than a single low-engagement post.
    """
    if not texts:
        return {
            'overall_label': 'neutral', 'overall_compound': 0.0,
            'positive_share': 0.0, 'negative_share': 0.0, 'neutral_share': 1.0,
            'n': 0, 'per_item': [],
        }

    weights = weights or [1.0] * len(texts)
    per_item = [classify_text(t) for t in texts]

    total_weight = sum(weights) or 1.0
    weighted_compound = sum(r['compound'] * w for r, w in zip(per_item, weights)) / total_weight

    label_weights = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
    for r, w in zip(per_item, weights):
        label_weights[r['label']] += w

    if weighted_compound >= 0.05:
        overall_label = 'positive'
    elif weighted_compound <= -0.05:
        overall_label = 'negative'
    else:
        overall_label = 'neutral'

    return {
        'overall_label': overall_label,
        'overall_compound': round(weighted_compound, 4),
        'positive_share': round(label_weights['positive'] / total_weight, 4),
        'negative_share': round(label_weights['negative'] / total_weight, 4),
        'neutral_share': round(label_weights['neutral'] / total_weight, 4),
        'n': len(texts),
        'per_item': per_item,
    }


if __name__ == "__main__":
    samples = [
        "AAPL to the moon! Diamond hands, earnings beat expectations 🚀",
        "Selling my position, this stock is a bagholder's nightmare",
        "Holding steady, nothing new to report this quarter",
    ]
    for s in samples:
        print(s, '->', classify_text(s))
    print('batch:', classify_batch(samples, weights=[10, 5, 1]))
