from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies.database import get_db
from smarthunt.auth.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from smarthunt.auth.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# تعريف الـ Dependency باستخدام Annotated لتفادي تحذيرات B008 ولأجل كود أنظف
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: DatabaseSession):
    """تسجيل مستخدم جديد والتعامل مع تكرار البيانات"""
    try:
        user = await AuthService(db).register(
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
        )
        return user
    except IntegrityError:
        # إضافة from None أو from err لإرضاء قاعدة B904 ومنع الـ Exception Chaining المزعج
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered.",
        ) from None


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: DatabaseSession):
    """تسجيل الدخول وتوليد الـ JWT Token"""
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
