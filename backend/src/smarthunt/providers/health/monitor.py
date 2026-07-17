from __future__ import annotations

from datetime import datetime
from threading import Lock


class ProviderHealthMonitor:

    def __init__(self):

        self._status = {}
        self._lock = Lock()

    def success(self, provider: str):

        with self._lock:

            self._status[provider] = {
                "healthy": True,
                "last_success": datetime.utcnow().isoformat(),
                "last_failure": self._status.get(provider, {}).get("last_failure"),
            }

    def failure(self, provider: str):

        with self._lock:

            self._status[provider] = {
                "healthy": False,
                "last_success": self._status.get(provider, {}).get("last_success"),
                "last_failure": datetime.utcnow().isoformat(),
            }

    def status(self):

        return dict(self._status)


monitor = ProviderHealthMonitor()
