# utils/political.py - shared helpers for cross-referencing political data
"""
Name formatting differs across every public data source we touch (Congress.gov
gives "Cruz, Ted [R-TX]", Stock Watcher gives "Ted Cruz", FEC gives
"CRUZ, TED"), so both analysis/political_network.py (per-ticker deep dive)
and analysis/political_web.py (multi-company graph) share the same
token-overlap heuristic matcher rather than each rolling their own.
"""

import re
from typing import Any, Dict, Optional

_STOPWORDS = {
    'senator', 'sen', 'representative', 'rep', 'dr', 'mr', 'mrs', 'ms',
    'jr', 'sr', 'ii', 'iii', 'iv', 'honorable', 'hon', 'the',
}


def name_tokens(name: Optional[str]) -> set:
    if not name:
        return set()
    cleaned = re.sub(r'\[.*?\]', '', name)  # strip party/state tags like "[R-TX]"
    cleaned = re.sub(r'[^a-zA-Z\s,]', '', cleaned).lower()
    tokens = re.split(r'[\s,]+', cleaned)
    return {t for t in tokens if len(t) >= 4 and t not in _STOPWORDS}


def names_possibly_match(name_a: Optional[str], name_b: Optional[str]) -> bool:
    return bool(name_tokens(name_a) & name_tokens(name_b))


def bill_label(bill: Dict[str, Any]) -> str:
    return f"{(bill.get('bill_type') or '').upper()} {bill.get('bill_number') or '?'}"
