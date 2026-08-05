from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/search-provider")
async def search_provider(
    provider: str,
    query: str,
    location: str | None = None,
    # Lower than discover()'s default 25 — measured live 2026-08-04:
    # LinkedIn's real search visits each job's own detail page for its
    # description (~4.3s/job), so 25 jobs would take ~110s, past what an
    # interactive "search this site now" click should reasonably wait.
    limit: int = 15,
    db: AsyncSession = Depends(get_db),
):
    """ "Search this specific site" — live-searches exactly one named
    provider's own site instead of only ever searching the local jobs
    table. No forced Saudi-only location filter (the caller's own
    location, if any, is respected as-is), but the same strict
    title-relevance filter as discover() still applies — see
    DiscoveryService.search_single_provider for why."""
    service = DiscoveryService(db)

    try:
        return await service.search_single_provider(
            provider_name=provider,
            query=query,
            location=location,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
