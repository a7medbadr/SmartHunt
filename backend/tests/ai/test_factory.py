from smarthunt.ai.factory import AIProviderFactory
from smarthunt.ai.providers.local_llm import LocalLLMProvider
from smarthunt.ai.types import AIProvider


def test_factory_returns_provider():

    provider = AIProviderFactory.get(
        AIProvider.LOCAL,
    )

    assert isinstance(
        provider,
        LocalLLMProvider,
    )


def test_factory_available_providers():

    providers = AIProviderFactory.available_providers()

    assert AIProvider.OPENAI in providers
    assert AIProvider.LOCAL in providers


def test_factory_register():

    provider = LocalLLMProvider()

    AIProviderFactory.register(
        AIProvider.LOCAL,
        provider,
    )

    result = AIProviderFactory.get(
        AIProvider.LOCAL,
    )

    assert result is provider
