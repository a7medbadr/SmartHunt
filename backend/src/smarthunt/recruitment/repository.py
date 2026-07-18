from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.recruitment.models import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, app_data: dict) -> Application:
        application = Application(**app_data)
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_all(self) -> list[Application]:
        stmt = select(Application).order_by(Application.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, app_id: str) -> Application | None:
        stmt = select(Application).where(Application.id == app_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, application: Application, new_status: ApplicationStatus
    ) -> Application:
        application.status = new_status
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def delete(self, application: Application) -> None:
        await self.session.delete(application)
        await self.session.commit()
