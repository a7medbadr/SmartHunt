from __future__ import annotations

from time import time


class SearchCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        item = self._cache.get(key)
        if not item:
            return None
        expire, value = item
        if expire < time():
            del self._cache[key]
            return None
        return value

    def set(self, key, value, ttl=60):
        self._cache[key] = (
            time() + ttl,
            value,
        )


cache = SearchCache()
