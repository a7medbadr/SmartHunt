from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.browser.session.models import BrowserSession
from smarthunt.browser.session.schemas import BrowserSessionCreate


class BrowserSessionNotFoundError(Exception):
    pass


class BrowserSessionService:
    async def open(self, db: AsyncSession, data: BrowserSessionCreate) -> BrowserSession:
        session = BrowserSession(provider=data.provider, status="ACTIVE")
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    async def list_all(self, db: AsyncSession) -> List[BrowserSession]:
        result = await db.execute(
            select(BrowserSession).order_by(BrowserSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, session_id: int) -> BrowserSession:
        result = await db.execute(
            select(BrowserSession).where(BrowserSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise BrowserSessionNotFoundError(f"Browser session with id {session_id} not found")
        return session

    async def close(self, db: AsyncSession, session_id: int) -> BrowserSession:
        session = await self.get(db, session_id)
        session.status = "CLOSED"
        session.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.flush()
        await db.refresh(session)
        return session


browser_session_service = BrowserSessionService()
