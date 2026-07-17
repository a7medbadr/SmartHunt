from fastapi import APIRouter

from smarthunt.search.history import all

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search History"],
)


@router.get("/history")
async def history():
    return {
        "items": all(),
        "count": len(all()),
    }
