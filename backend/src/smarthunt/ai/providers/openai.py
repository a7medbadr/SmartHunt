from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.core.config import settings


class OpenAIProvider(BaseAIProvider):

    name = AIProvider.OPENAI

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.openai_api_key:
            raise AIProviderError("OpenAI API key is not configured")

        try:
            return AIResponse(
                provider=self.name,
                content=request.prompt,
                success=True,
            )

        except Exception as exc:
            raise AIProviderError(f"OpenAI provider failed: {exc}") from exc
