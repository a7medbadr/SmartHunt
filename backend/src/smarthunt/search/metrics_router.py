from fastapi import APIRouter

from smarthunt.search.metrics import metrics

router = APIRouter(
    prefix="/search",
    tags=["Search Metrics"],
)


@router.get("/metrics/details")
async def metrics_details():
    return metrics.summary()
