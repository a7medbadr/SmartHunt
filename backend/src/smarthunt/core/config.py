from functools import lru_cache

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartHunt"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    app_name: str = "SmartHunt"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = False

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

    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "access_token_expire_minutes",
        ),
    )

    BACKEND_CORS_ORIGINS: list[str] = []

    @computed_field
    @property
    def test_database_url(self) -> str:
        return self.database_url.replace(
            "/smarthunt",
            "/smarthunt_test",
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
