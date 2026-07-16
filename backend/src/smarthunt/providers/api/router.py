from fastapi import APIRouter
from smarthunt.providers.registry.registry import ProviderRegistry

router = APIRouter()
registry = ProviderRegistry()

@router.get("/")
async def providers():
    items = []
    for provider in registry.providers():
        items.append(
            {
                "name": provider.name,
                "supports_login": provider.supports_login,
                "supports_apply": provider.supports_apply,
                "supports_resume_upload": provider.supports_resume_upload,
                "supports_cover_letter": provider.supports_cover_letter,
            }
        )
    return {"items": items}
