from smarthunt.providers.base.provider import JobProvider

class ProviderRegistry:
    def __init__(self):
        self.providers: dict[str, JobProvider] = {}

    def register(self, provider: JobProvider):
        self.providers[provider.name] = provider

    def get(self, name: str):
        return self.providers.get(name)

    def all(self):
        return list(self.providers.values())
