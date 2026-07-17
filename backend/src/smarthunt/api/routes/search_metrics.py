from fastapi import APIRouter

from smarthunt.search.metrics import metrics

router = APIRouter(tags=["Search Metrics"])


@router.get("/search/metrics")
async def get_search_metrics():
    return {"total_searches": metrics.total_searches}
