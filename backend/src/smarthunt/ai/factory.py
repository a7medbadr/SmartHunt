from threading import Lock

from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.providers.anthropic import AnthropicProvider
from smarthunt.ai.providers.azure_openai import AzureOpenAIProvider
from smarthunt.ai.providers.local_llm import LocalLLMProvider
from smarthunt.ai.providers.ollama import OllamaProvider
from smarthunt.ai.providers.openai import OpenAIProvider
from smarthunt.ai.types import AIProvider


class AIProviderFactory:

    _lock = Lock()

    _provider_classes = {
        AIProvider.OPENAI: OpenAIProvider,
        AIProvider.AZURE_OPENAI: AzureOpenAIProvider,
        AIProvider.ANTHROPIC: AnthropicProvider,
        AIProvider.OLLAMA: OllamaProvider,
        AIProvider.LOCAL: LocalLLMProvider,
    }

    _providers: dict[AIProvider, BaseAIProvider] = {}


    @classmethod
    def get(
        cls,
        provider: AIProvider,
    ) -> BaseAIProvider:

        if provider in cls._providers:
            return cls._providers[provider]

        with cls._lock:

            if provider not in cls._providers:

                implementation = cls._provider_classes.get(
                    provider
                )

                if implementation is None:
                    raise ValueError(
                        f"Unsupported AI provider {provider}"
                    )

                cls._providers[provider] = implementation()

        return cls._providers[provider]


    @classmethod
    def register(
        cls,
        provider: AIProvider,
        implementation: BaseAIProvider,
    ) -> None:

        with cls._lock:
            cls._providers[provider] = implementation


    @classmethod
    def available_providers(
        cls,
    ) -> list[AIProvider]:

        return list(
            cls._provider_classes.keys()
        )
