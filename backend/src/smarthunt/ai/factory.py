from threading import Lock
from typing import Callable

from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.providers.anthropic import AnthropicProvider
from smarthunt.ai.providers.azure_openai import AzureOpenAIProvider
from smarthunt.ai.providers.local_llm import LocalLLMProvider
from smarthunt.ai.providers.ollama import OllamaProvider
from smarthunt.ai.providers.openai import OpenAIProvider
from smarthunt.ai.types import AIProvider


class AIProviderFactory:

    _lock = Lock()

    _registry: dict[
        AIProvider,
        Callable[[], BaseAIProvider]
    ] = {
        AIProvider.OPENAI: OpenAIProvider,
        AIProvider.AZURE_OPENAI: AzureOpenAIProvider,
        AIProvider.ANTHROPIC: AnthropicProvider,
        AIProvider.OLLAMA: OllamaProvider,
        AIProvider.LOCAL: LocalLLMProvider,
    }

    _instances: dict[
        AIProvider,
        BaseAIProvider
    ] = {}


    @classmethod
    def get(
        cls,
        provider: AIProvider,
    ) -> BaseAIProvider:

        if provider in cls._instances:
            return cls._instances[provider]

        with cls._lock:

            if provider not in cls._instances:

                implementation = cls._registry.get(
                    provider
                )

                if implementation is None:
                    raise ValueError(
                        f"Unsupported AI provider {provider}"
                    )

                cls._instances[provider] = implementation()

        return cls._instances[provider]


    @classmethod
    def register(
        cls,
        provider: AIProvider,
        implementation: Callable[[], BaseAIProvider],
    ) -> None:

        with cls._lock:
            cls._registry[provider] = implementation
            cls._instances.pop(
                provider,
                None,
            )
