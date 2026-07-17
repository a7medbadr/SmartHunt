from __future__ import annotations

from datetime import datetime, timezone


class SearchMetrics:
    def __init__(self):
        self.total_searches = 0
        self.cached_hits = 0
        self.provider_calls = 0
        self.total_results = 0
        self.last_search_time: str | None = None

    def search(self, results_count: int = 0):
        self.total_searches += 1
        self.total_results += results_count
        self.last_search_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def cache_hit(self):
        self.cached_hits += 1

    def provider_call(self):
        self.provider_calls += 1

    def summary(self):
        avg = round(self.total_results / self.total_searches, 2) if self.total_searches > 0 else 0.0
        return {
            "total_searches": self.total_searches,
            "cached_hits": self.cached_hits,
            "provider_calls": self.provider_calls,
            "average_results": avg,
            "last_search_time": self.last_search_time,
        }


metrics = SearchMetrics()
