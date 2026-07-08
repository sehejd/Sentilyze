# utils/cache.py - lightweight disk cache for slow/rate-limited external data
"""
Simple JSON file cache with a TTL. Used to avoid hammering free public APIs
(SEC EDGAR, Senate/House Stock Watcher, GDELT, Google Trends) that either rate
limit aggressively or serve multi-megabyte datasets that don't change often.

Not a replacement for a real cache (Redis/etc.) - this is a personal-use app
running a single Flask process, so a file on disk is enough.
"""

import json
import os
import time
import hashlib
from typing import Any, Callable, Optional

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cache')


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:24]
    safe_key = ''.join(c for c in key if c.isalnum() or c in ('-', '_'))[:60]
    return os.path.join(CACHE_DIR, f"{safe_key}_{digest}.json")


def cache_get(key: str, ttl_seconds: int) -> Optional[Any]:
    """Return cached value for key if present and not expired, else None."""
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            envelope = json.load(f)
        if time.time() - envelope.get('cached_at', 0) > ttl_seconds:
            return None
        return envelope.get('data')
    except (json.JSONDecodeError, OSError):
        return None


def cache_set(key: str, data: Any) -> None:
    path = _cache_path(key)
    try:
        with open(path, 'w') as f:
            json.dump({'cached_at': time.time(), 'data': data}, f)
    except OSError:
        pass


def cached_fetch(key: str, ttl_seconds: int, fetch_fn: Callable[[], Any]) -> Any:
    """Fetch-through cache helper: return cached data or call fetch_fn and store it."""
    cached = cache_get(key, ttl_seconds)
    if cached is not None:
        return cached
    data = fetch_fn()
    cache_set(key, data)
    return data
