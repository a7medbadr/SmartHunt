from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies.database import get_db
from smarthunt.auth.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from smarthunt.auth.security import get_current_user
from smarthunt.auth.services.auth_service import AuthService
from smarthunt.database.models.user import User

router = APIRouter(tags=["Authentication"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: DatabaseSession):
    try:
        return await AuthService(db).register(
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered.",
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: DatabaseSession):
    token = await AuthService(db).login(
        username=user_in.username,
        password=user_in.password,
    )
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me(current_user: CurrentUser):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }
