from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)


class AnthropicProvider(BaseAIProvider):

    name = AIProvider.ANTHROPIC


    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        return AIResponse(
            provider=self.name,
            content=request.prompt,
            success=True,
        )
