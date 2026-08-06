from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.linkedin_monitor import service
from smarthunt.linkedin_monitor.post_scanner import (
    LinkedInScanError,
    scan_hashtag_posts,
    scan_home_feed,
    scan_profile_posts,
)
from smarthunt.linkedin_monitor.schemas import (
    MonitoredAccountCreate,
    MonitoredAccountResponse,
    MonitoredAccountUpdate,
    MonitoredHashtagCreate,
    MonitoredHashtagResponse,
    MonitoredHashtagUpdate,
    ScanResultResponse,
)

router = APIRouter(prefix="/linkedin-monitor", tags=["linkedin-monitor"])


@router.get("/hashtags", response_model=list[MonitoredHashtagResponse])
async def list_hashtags(db: AsyncSession = Depends(get_db)):
    """The owner's own, DB-backed hashtag list — moved 2026-08-06 from a
    hardcoded Python list to a real table (see linkedin_monitor/models.py's
    MonitoredHashtag) so each hashtag can be added/removed/enabled from
    the job-search page directly, the same as monitored accounts below,
    instead of only being editable by changing code."""
    return await service.list_hashtags(db)


@router.post(
    "/hashtags", response_model=MonitoredHashtagResponse, status_code=status.HTTP_201_CREATED
)
async def add_hashtag(payload: MonitoredHashtagCreate, db: AsyncSession = Depends(get_db)):
    return await service.add_hashtag(db, payload.tag)


@router.patch("/hashtags/{hashtag_id}", response_model=MonitoredHashtagResponse)
async def update_hashtag(
    hashtag_id: int, payload: MonitoredHashtagUpdate, db: AsyncSession = Depends(get_db)
):
    hashtag = await service.set_hashtag_enabled(db, hashtag_id, payload.enabled)
    if hashtag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found.")
    return hashtag


@router.delete("/hashtags/{hashtag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hashtag(hashtag_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await service.remove_hashtag(db, hashtag_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found.")


@router.post("/hashtags/{hashtag_id}/scan", response_model=ScanResultResponse)
async def scan_hashtag(hashtag_id: int, db: AsyncSession = Depends(get_db)):
    """Manual trigger for a single hashtag — mirrors scan_account below
    exactly, replacing the old bulk POST /scan-hashtags (which took an
    arbitrary hashtag list from the request body) now that hashtags are
    individually addressable DB rows with their own "scan now" button."""
    hashtags = await service.list_hashtags(db)
    hashtag = next((h for h in hashtags if h.id == hashtag_id), None)
    if hashtag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found.")

    try:
        posts = await scan_hashtag_posts(hashtag.tag)
    except LinkedInScanError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.reason) from exc

    saved = await service.scan_and_save(db, posts)
    await service.mark_hashtag_checked(db, hashtag_id)

    return ScanResultResponse(
        scanned=len(posts), saved=len(saved), job_ids=[job.id for job in saved]
    )


@router.get("/accounts", response_model=list[MonitoredAccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    return await service.list_accounts(db)


@router.post(
    "/accounts", response_model=MonitoredAccountResponse, status_code=status.HTTP_201_CREATED
)
async def add_account(payload: MonitoredAccountCreate, db: AsyncSession = Depends(get_db)):
    return await service.add_account(db, payload.profile_url, payload.label)


@router.patch("/accounts/{account_id}", response_model=MonitoredAccountResponse)
async def update_account(
    account_id: int, payload: MonitoredAccountUpdate, db: AsyncSession = Depends(get_db)
):
    account = await service.set_account_enabled(db, account_id, payload.enabled)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await service.remove_account(db, account_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")


@router.post("/accounts/{account_id}/scan", response_model=ScanResultResponse)
async def scan_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Manual trigger only — deliberately not on the automatic scheduler
    yet (see post_scanner.py's module docstring for why: this needs the
    authenticated LinkedIn session, and today's account already hit a
    real login checkpoint from unrelated activity earlier)."""
    accounts = await service.list_accounts(db)
    account = next((a for a in accounts if a.id == account_id), None)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    try:
        posts = await scan_profile_posts(account.profile_url)
    except LinkedInScanError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.reason) from exc

    saved = await service.scan_and_save(db, posts)
    await service.mark_account_checked(db, account_id)

    return ScanResultResponse(
        scanned=len(posts), saved=len(saved), job_ids=[job.id for job in saved]
    )


@router.post("/scan-feed", response_model=ScanResultResponse)
async def scan_feed(db: AsyncSession = Depends(get_db)):
    """Manual trigger only — see scan_account's docstring."""
    try:
        posts = await scan_home_feed()
    except LinkedInScanError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.reason) from exc

    saved = await service.scan_and_save(db, posts)

    return ScanResultResponse(
        scanned=len(posts), saved=len(saved), job_ids=[job.id for job in saved]
    )
