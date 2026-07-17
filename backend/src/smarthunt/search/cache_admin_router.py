from fastapi import APIRouter

from smarthunt.search.cache import cache

router = APIRouter(
    prefix="/search",
    tags=["Search Cache Admin"],
)


@router.delete("/cache")
async def clear_cache():
    cache._cache.clear()
    return {
        "status": "cleared",
        "cached_queries": len(cache._cache),
    }
