from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db
from smarthunt.discovery.service import DiscoveryService

router = APIRouter(
    prefix="/discovery",
    tags=["discovery"],
)

# Saudi Arabia only, per the project owner's explicit requirement (kept
# in sync with scheduler/jobs.py's DISCOVERY_LOCATION) — a manual run
# with no location specified shouldn't silently search everywhere.
DEFAULT_LOCATION = "Saudi Arabia"


@router.post("/run")
async def run_discovery(
    query: str,
    location: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)

    return await service.discover(
        query=query,
        location=location or DEFAULT_LOCATION,
    )
