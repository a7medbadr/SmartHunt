from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.linkedin_monitor import service
from smarthunt.linkedin_monitor.post_scanner import (
    scan_hashtag_posts,
    scan_home_feed,
    scan_profile_posts,
)
from smarthunt.linkedin_monitor.schemas import (
    HashtagScanRequest,
    MonitoredAccountCreate,
    MonitoredAccountResponse,
    MonitoredAccountUpdate,
    ScanResultResponse,
)

router = APIRouter(prefix="/linkedin-monitor", tags=["linkedin-monitor"])


@router.get("/hashtags", response_model=list[str])
async def list_hashtags():
    """The owner's curated hashtag list, same list scan_hashtags_daily
    (scheduler/jobs.py) sweeps once a day — exposed here so the
    job-search page's per-hashtag scan buttons stay in sync with it
    instead of duplicating the list client-side."""
    from smarthunt.scheduler.jobs import HASHTAG_LIST

    return HASHTAG_LIST


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

    posts = await scan_profile_posts(account.profile_url)
    saved = await service.scan_and_save(db, posts)
    await service.mark_account_checked(db, account_id)

    return ScanResultResponse(
        scanned=len(posts), saved=len(saved), job_ids=[job.id for job in saved]
    )


@router.post("/scan-feed", response_model=ScanResultResponse)
async def scan_feed(db: AsyncSession = Depends(get_db)):
    """Manual trigger only — see scan_account's docstring."""
    posts = await scan_home_feed()
    saved = await service.scan_and_save(db, posts)

    return ScanResultResponse(
        scanned=len(posts), saved=len(saved), job_ids=[job.id for job in saved]
    )


@router.post("/scan-hashtags", response_model=ScanResultResponse)
async def scan_hashtags(payload: HashtagScanRequest, db: AsyncSession = Depends(get_db)):
    """Manual trigger — scans each given hashtag's first ~50 posts (owner
    supplies the hashtag list from the job-search page), aggregating
    scanned/saved counts across all of them into one response."""
    total_scanned = 0
    all_saved = []
    for hashtag in payload.hashtags:
        posts = await scan_hashtag_posts(hashtag)
        total_scanned += len(posts)
        all_saved.extend(await service.scan_and_save(db, posts))

    return ScanResultResponse(
        scanned=total_scanned,
        saved=len(all_saved),
        job_ids=[job.id for job in all_saved],
    )
