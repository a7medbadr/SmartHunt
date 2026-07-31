from smarthunt.ai.factory import AIProviderFactory
from smarthunt.ai.types import AIProviderHealth


async def ai_health_check() -> dict:

    providers = []

    for provider in AIProviderFactory.available_providers():

        providers.append(
            AIProviderHealth(
                provider=provider,
                available=True,
            ).model_dump()
        )

    return {
        "status": "healthy",
        "providers": providers,
    }
