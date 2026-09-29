"""
CacheService — a tiny TTL cache.

Backed by a plain dict for now. The interface (get/set/clear) is the same
shape a Redis-backed implementation would expose, so swapping the backend
later (e.g. `RedisCacheService`) doesn't require touching call sites.
"""

import time
import hashlib
import threading
from typing import Any, Optional


class CacheService:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at is not None and time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expires_at = (time.time() + ttl) if ttl else None
        with self._lock:
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._store)


def make_summary_cache_key(article_url: str) -> str:
    """hash(article_url + 'summary') — stable, fixed-length cache key."""
    raw = f"{article_url}:summary".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# Module-level singleton used by the app (simple, sufficient for a single
# process; swap for a shared Redis instance if running multiple workers).
cache = CacheService()
