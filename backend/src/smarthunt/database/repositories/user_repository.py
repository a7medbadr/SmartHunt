from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.user import User
from smarthunt.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username_or_email(
        self,
        *,
        username: str,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        )
        return result.scalar_one_or_none()
