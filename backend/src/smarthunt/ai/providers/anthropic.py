from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.core.config import settings


class AnthropicProvider(BaseAIProvider):

    name = AIProvider.ANTHROPIC

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.anthropic_api_key:
            raise AIProviderError("Anthropic API key is not configured")

        try:
            return AIResponse(
                provider=self.name,
                content=request.prompt,
                success=True,
            )

        except Exception as exc:
            raise AIProviderError(f"Anthropic provider failed: {exc}") from exc
