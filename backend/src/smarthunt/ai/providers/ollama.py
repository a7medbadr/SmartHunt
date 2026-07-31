from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.core.config import settings


class OllamaProvider(BaseAIProvider):

    name = AIProvider.OLLAMA

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.ollama_url:
            raise AIProviderError(
                "Ollama URL is not configured"
            )

        try:
            return AIResponse(
                provider=self.name,
                content=f"[OLLAMA] {request.prompt}",
                success=True,
            )

        except Exception as exc:
            raise AIProviderError(
                f"Ollama provider failed: {exc}"
            ) from exc
