from __future__ import annotations


class SearchMetrics:
    def __init__(self):
        self.total_searches = 0
        self.cached_hits = 0
        self.provider_calls = 0

    def search(self):
        self.total_searches += 1

    def cache_hit(self):
        self.cached_hits += 1

    def provider_call(self):
        self.provider_calls += 1

    def summary(self):
        return {
            "total_searches": self.total_searches,
            "cached_hits": self.cached_hits,
            "provider_calls": self.provider_calls,
        }


metrics = SearchMetrics()
