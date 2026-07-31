from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)


class LocalLLMProvider(BaseAIProvider):

    name = AIProvider.LOCAL

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        try:
            return AIResponse(
                provider=self.name,
                content=f"[LOCAL LLM] {request.prompt}",
                success=True,
            )

        except Exception as exc:
            raise AIProviderError(f"Local LLM provider failed: {exc}") from exc
