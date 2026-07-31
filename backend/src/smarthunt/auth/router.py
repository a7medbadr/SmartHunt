from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.auth.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from smarthunt.auth.security import get_current_user
from smarthunt.auth.services.auth_service import AuthService
from smarthunt.database.models.user import User
from smarthunt.database.session import get_db

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: DB):
    service = AuthService(db)

    user = await service.register(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: DB):
    service = AuthService(db)

    token = await service.login(
        username=credentials.username,
        password=credentials.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return TokenResponse(access_token=token)


@router.post("/token", response_model=TokenResponse)
async def get_token(credentials: UserLogin, db: DB):
    return await login(credentials, db)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser):
    return current_user
