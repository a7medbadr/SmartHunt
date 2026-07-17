from fastapi import APIRouter

from smarthunt.search.metrics import total

router = APIRouter(prefix="/search", tags=["Search Metrics"])


@router.get("/metrics")
async def metrics():
    return {
        "total_searches": total()
    }
