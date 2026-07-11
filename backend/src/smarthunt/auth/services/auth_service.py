from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.auth.security.jwt import create_access_token
from smarthunt.auth.security.password import (
    hash_password,
    verify_password,
)
from smarthunt.database.models.user import User
from smarthunt.database.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(
        self,
        username: str,
        email: str,
        password: str,
    ):
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )

        return await self.repository.create(user)

    async def login(
        self,
        username: str,
        password: str,
    ):
        user = await self.repository.get_by_username(username)

        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # تمرير البيانات كـ Dictionary يحتوي على الـ sub ليتوافق مع دالة توليد الـ Token
        return create_access_token(data={"sub": user.username})
