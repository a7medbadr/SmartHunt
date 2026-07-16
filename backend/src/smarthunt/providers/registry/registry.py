from smarthunt.providers.base.provider import JobProvider

class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, JobProvider] = {}

    def register(self, provider: JobProvider):
        self._providers[provider.name] = provider

    def get(self, name: str) -> JobProvider | None:
        return self._providers.get(name)

    def all(self) -> list[JobProvider]:
        return list(self._providers.values())

    def enabled(self) -> list[str]:
        return list(self._providers.keys())
