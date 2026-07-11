from typing import Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic repository."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    async def get(self, object_id: int) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == object_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, object_id: int) -> None:
        stmt = delete(self.model).where(self.model.id == object_id)
        await self.session.execute(stmt)
        await self.session.commit()
