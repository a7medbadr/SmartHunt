from smarthunt.browser.providers.mock_provider import MockProvider
from smarthunt.browser.providers.mock_provider2 import MockProvider2


class ProviderRegistry:

    def __init__(self):

        self.providers = [
            MockProvider(),
            MockProvider2(),
        ]

    def get_all(self):
        return self.providers
