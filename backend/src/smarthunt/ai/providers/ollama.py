import httpx

from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError, AITimeoutError
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
            raise AIProviderError("Ollama URL is not configured")

        payload = {
            "model": settings.ollama_model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=request.timeout) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            return AIResponse(
                provider=self.name,
                content=data.get("response", ""),
                success=True,
            )

        except httpx.TimeoutException as exc:
            raise AITimeoutError(f"Ollama request timed out: {exc}") from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(f"Ollama provider failed: {exc}") from exc
