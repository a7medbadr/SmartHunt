from functools import lru_cache

from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartHunt"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    app_name: str = "SmartHunt"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = False
    build_version: str = "latest"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str
    redis_url: str

    openai_api_key: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    linkedin_email: str | None = None
    linkedin_password: str | None = None

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

    enable_playwright: bool = True
    enable_notifications: bool = True
    enable_ai_services: bool = True

    security_headers_enabled: bool = True

    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {
            "development",
            "testing",
            "test",
            "staging",
            "production",
        }

        if value not in allowed:
            raise ValueError(
                f"Invalid environment: {value}"
            )

        return value

    def model_post_init(self, __context) -> None:
        if self.app_env == "production":
            required = {
                "database_url": self.database_url,
                "secret_key": self.secret_key,
                "jwt_secret_key": self.jwt_secret_key,
            }

            missing = [
                key
                for key, value in required.items()
                if not value
            ]

            if missing:
                raise ValueError(
                    f"Missing production configuration: {missing}"
                )

            if self.app_debug:
                raise ValueError(
                    "DEBUG must be disabled in production"
                )

    @computed_field
    @property
    def test_database_url(self) -> str:
        return self.database_url.replace(
            "/smarthunt",
            "/smarthunt_test",
        )

    @computed_field
    @property
    def environment(self) -> str:
        return self.app_env

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
