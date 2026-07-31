import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.application import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Application]:
        result = await self.session.execute(
            select(Application).order_by(Application.created_at.desc())
        )
        return list(result.scalars())

    async def get(self, application_id: uuid.UUID) -> Application | None:
        result = await self.session.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Application:
        application = Application(**kwargs)
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def update(self, application: Application, **kwargs) -> Application:
        for key, value in kwargs.items():
            if value is not None:
                setattr(application, key, value)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def delete(self, application: Application) -> None:
        await self.session.delete(application)
        await self.session.commit()
