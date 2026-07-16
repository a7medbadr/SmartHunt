from __future__ import annotations
from datetime import datetime

class ProviderHealthMonitor:
    def __init__(self):
        self._status = {}

    def success(self, provider: str):
        self._status[provider] = {
            "healthy": True,
            "last_success": datetime.utcnow().isoformat(),
            "last_failure": self._status.get(provider, {}).get("last_failure"),
        }

    def failure(self, provider: str):
        self._status[provider] = {
            "healthy": False,
            "last_success": self._status.get(provider, {}).get("last_success"),
            "last_failure": datetime.utcnow().isoformat(),
        }

    def all(self):
        return self._status
