from smarthunt.browser.registry.registry import ProviderRegistry


class ProviderService:

    def __init__(self):
        self.registry = ProviderRegistry()

    def status(self):
        return [
            {
                "name": provider.name,
            }
            for provider in self.registry.get_all()
        ]
