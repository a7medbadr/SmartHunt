from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.types import AIProvider, AIRequest, AIResponse


class OllamaProvider(BaseAIProvider):
    name = AIProvider.OLLAMA

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
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
