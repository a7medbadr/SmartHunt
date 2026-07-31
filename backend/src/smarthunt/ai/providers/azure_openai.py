from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)


class AzureOpenAIProvider(BaseAIProvider):

    name = AIProvider.AZURE_OPENAI


    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        return AIResponse(
            provider=self.name,
            content=request.prompt,
            success=True,
        )
