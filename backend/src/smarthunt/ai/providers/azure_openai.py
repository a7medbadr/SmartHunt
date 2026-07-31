from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.core.config import settings


class AzureOpenAIProvider(BaseAIProvider):

    name = AIProvider.AZURE_OPENAI

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.azure_openai_api_key:
            raise AIProviderError("Azure OpenAI API key is not configured")

        if not settings.azure_openai_endpoint:
            raise AIProviderError("Azure OpenAI endpoint is not configured")

        try:
            return AIResponse(
                provider=self.name,
                content=request.prompt,
                success=True,
            )

        except Exception as exc:
            raise AIProviderError(f"Azure OpenAI provider failed: {exc}") from exc
