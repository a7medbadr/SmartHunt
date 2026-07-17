from fastapi import APIRouter

from smarthunt.search.history import all, clear

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search History"],
)


@router.get("/history")
async def history():
    items = all()
    return {
        "items": items,
        "count": len(items),
    }


@router.delete("/history")
async def clear_history():
    clear()
    items = all()
    return {
        "status": "cleared",
        "searches": len(items),
    }
