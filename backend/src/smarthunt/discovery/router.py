from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db
from smarthunt.discovery.service import DiscoveryService

router = APIRouter(
    prefix="/discovery",
    tags=["discovery"],
)


@router.post("/run")
async def run_discovery(
    query: str,
    location: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)

    return await service.discover(
        query=query,
        location=location,
    )
