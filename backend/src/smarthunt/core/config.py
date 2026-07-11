from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartHunt"

    debug: bool = True

    database_url: str

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    access_token_expire_hours: int = 24

    playwright_headless: bool = True

    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
