import httpx

from smarthunt.ai.factory import AIProviderFactory
from smarthunt.ai.types import AIProvider, AIProviderHealth
from smarthunt.core.config import settings


async def _check_provider(provider: AIProvider) -> AIProviderHealth:
    if provider == AIProvider.OPENAI:
        return AIProviderHealth(
            provider=provider,
            available=bool(settings.openai_api_key),
            message=None if settings.openai_api_key else "OPENAI_API_KEY not configured",
        )

    if provider == AIProvider.AZURE_OPENAI:
        configured = bool(settings.azure_openai_endpoint and settings.azure_openai_api_key)
        return AIProviderHealth(
            provider=provider,
            available=configured,
            message=None if configured else "Azure OpenAI endpoint/key not configured",
        )

    if provider == AIProvider.ANTHROPIC:
        return AIProviderHealth(
            provider=provider,
            available=bool(settings.anthropic_api_key),
            message=None if settings.anthropic_api_key else "ANTHROPIC_API_KEY not configured",
        )

    if provider == AIProvider.OLLAMA:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{settings.ollama_url}/api/version")
                response.raise_for_status()
            return AIProviderHealth(provider=provider, available=True)
        except httpx.HTTPError as exc:
            return AIProviderHealth(
                provider=provider,
                available=False,
                message=f"Ollama unreachable at {settings.ollama_url}: {exc}",
            )

    return AIProviderHealth(provider=provider, available=True)


async def ai_health_check() -> dict:
    providers = [
        (await _check_provider(provider)).model_dump()
        for provider in AIProviderFactory.available_providers()
    ]

    return {
        "status": "healthy" if any(p["available"] for p in providers) else "degraded",
        "providers": providers,
    }
