from sqlalchemy import select

from smarthunt.database.models.user import User
from smarthunt.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_username(self, username: str):
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
