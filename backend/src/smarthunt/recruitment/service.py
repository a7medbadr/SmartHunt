from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.application import Application
from smarthunt.recruitment.schemas import ApplicationCreate


class RecruitmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_application(self, payload: ApplicationCreate) -> Application:
        app = Application(
            job_title=payload.job_title,
            company=payload.company,
            url=str(payload.url) if payload.url else None,
            status=payload.status,
        )
        self.session.add(app)
        await self.session.commit()
        await self.session.refresh(app)
        return app

    async def list_applications(self) -> List[Application]:
        result = await self.session.execute(select(Application))
        return list(result.scalars().all())

    async def update_status(
        self, app_id: UUID, status: str
    ) -> Optional[Application]:
        result = await self.session.execute(
            select(Application).where(Application.id == app_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            return None

        app.status = status
        await self.session.commit()
        await self.session.refresh(app)
        return app

    async def delete_application(self, app_id: UUID) -> bool:
        result = await self.session.execute(
            select(Application).where(Application.id == app_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            return False

        await self.session.delete(app)
        await self.session.commit()
        return True
