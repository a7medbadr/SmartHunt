from __future__ import annotations

from time import time


class SearchCache:
    def __init__(self):
        self._cache = {}
        self.hits = 0
        self.misses = 0

    def get(self, key):
        item = self._cache.get(key)
        if not item:
            self.misses += 1
            return None
        expire, value = item
        if expire < time():
            del self._cache[key]
            self.misses += 1
            return None
        self.hits += 1
        return value

    def set(self, key, value, ttl=60):
        self._cache[key] = (
            time() + ttl,
            value,
        )

    def statistics(self):
        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
        }


cache = SearchCache()
