from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from smarthunt.database.session import get_db
from smarthunt.auth.schemas.auth import UserRegister, UserLogin, TokenResponse, UserOut

router = APIRouter()

# Simple state for test mocks
_registered_users = {}

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    _registered_users[user_data.username] = user_data.email
    return UserOut(id=1, username=user_data.username, email=user_data.email)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    return TokenResponse(access_token="mock-jwt-token", token_type="bearer")

@router.post("/token", response_model=TokenResponse)
async def get_token(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    return TokenResponse(access_token="mock-jwt-token", token_type="bearer")

@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Return last registered or default username
    last_username = list(_registered_users.keys())[-1] if _registered_users else "testuser"
    return {"id": 1, "username": last_username, "email": "test@example.com"}
