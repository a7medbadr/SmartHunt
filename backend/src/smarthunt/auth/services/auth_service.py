from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.auth.security.jwt import create_access_token
from smarthunt.auth.security.password import (
    hash_password,
    verify_password,
)
from smarthunt.database.models.user import User
from smarthunt.database.repositories.user_repository import UserRepository
from smarthunt.metrics import (
    login_attempts_total,
    users_registered_total,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(
        self,
        username: str,
        email: str,
        password: str,
    ) -> User:
        existing = await self.repository.get_by_username_or_email(
            username=username,
            email=email,
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or Email already registered.",
            )

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )

        created_user = await self.repository.create(user)

        users_registered_total.inc()

        return created_user

    async def login(
        self,
        username: str,
        password: str,
    ) -> str | None:
        login_attempts_total.inc()

        user = await self.repository.get_by_username(username)

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return create_access_token(
            data={
                "sub": user.username,
            }
        )

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="الباسورد الحالية غلط.",
            )

        user.password_hash = hash_password(new_password)
        await self.repository.session.commit()
