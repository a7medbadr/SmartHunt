from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.browser.session.schemas import BrowserSessionCreate, BrowserSessionResponse
from smarthunt.browser.session.service import (
    BrowserSessionNotFoundError,
    browser_session_service,
)

router = APIRouter(prefix="", tags=["browser-session"])


@router.post("", response_model=BrowserSessionResponse, status_code=status.HTTP_201_CREATED)
async def open_session(payload: BrowserSessionCreate, db: AsyncSession = Depends(get_db)):
    return await browser_session_service.open(db, payload)


@router.get("", response_model=List[BrowserSessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await browser_session_service.list_all(db)


@router.patch("/{session_id}/close", response_model=BrowserSessionResponse)
async def close_session(session_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await browser_session_service.close(db, session_id)
    except BrowserSessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
