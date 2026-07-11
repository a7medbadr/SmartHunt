from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from smarthunt.core.config import get_settings

settings = get_settings()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """توليد Access Token مشفر وموقع للمستخدم"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """فك تشفير الـ Token والتحقق من صلاحيته وأمانه"""
    try:
        decoded_token = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return decoded_token
    except jwt.PyJWTError:
        return None
