from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies.database import get_db
from smarthunt.auth.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from smarthunt.auth.security import create_access_token, get_current_user
from smarthunt.auth.services.auth_service import AuthService
from smarthunt.database.models.user import User

router = APIRouter(tags=["Authentication"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db),
]

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
)
async def register(
    user_in: UserRegister,
    db: DatabaseSession,
):
    return await AuthService(db).register(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    user_in: UserLogin,
    db: DatabaseSession,
):
    token = await AuthService(db).login(
        username=user_in.username,
        password=user_in.password,
    )

    if token is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
async def me(
    current_user: CurrentUser,
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    current_user: CurrentUser,
):
    """Issues a fresh token with a full new expiry window. Only reachable
    with a still-valid token — this is what makes the session sliding:
    the frontend calls it periodically while the user is active, so an
    active session never hits its expiry; an idle one just expires
    normally after ACCESS_TOKEN_EXPIRE_MINUTES with no calls to renew it."""
    token = create_access_token(data={"sub": current_user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
    }
