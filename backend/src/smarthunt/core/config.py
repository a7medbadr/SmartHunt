from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartHunt"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    redis_url: str

    openai_api_key: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Fields required by main.py (kept UPPER_CASE to match its usage) ---
    PROJECT_NAME: str = "SmartHunt"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
