from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.database.repositories.user_repository import UserRepository

SECRET_KEY = "CHANGE_ME_IN_ENV"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(hours=24),
) -> str:
    """
    توليد توكن الـ JWT باستقبال قاموس يحتوي على البيانات (data).
    """
    expire = datetime.now(UTC) + expires_delta

    # نأخذ نسخة من القاموس الممرر لتجنب التعديل على الكائن الأصلي
    payload = data.copy()
    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


DB = Annotated[AsyncSession, Depends(get_db)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(
    token: Token,
    db: DB,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = await UserRepository(db).get_by_username(username)

    if user is None:
        raise credentials_exception

    return user
