from fastapi import APIRouter

from smarthunt.search.cache import cache

router = APIRouter(
    prefix="/search",
    tags=["Search Cache"],
)


@router.get("/cache")
async def cache_info():
    return cache.statistics()
