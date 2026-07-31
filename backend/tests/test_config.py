import pytest

from smarthunt.core.config import Settings


def test_valid_configuration():
    settings = Settings(
        database_url="postgresql://user:pass@localhost/smarthunt",
        redis_url="redis://localhost:6379",
        secret_key="test-secret-key-32-characters-long-key-32-characters-long",
        jwt_secret_key="test-jwt-secret-key-with-more-than-32-characters-long-safe-safe",
        app_env="development",
    )

    assert settings.app_env == "development"
    assert settings.enable_playwright is True


def test_invalid_environment():
    with pytest.raises(ValueError):
        Settings(
            database_url="postgresql://user:pass@localhost/smarthunt",
            redis_url="redis://localhost:6379",
            secret_key="test-secret-key-32-characters-long-key-32-characters-long",
            jwt_secret_key="test-jwt-secret-key-with-more-than-32-characters-long-safe-safe",
            app_env="invalid",
        )


def test_production_debug_validation():
    with pytest.raises(ValueError):
        Settings(
            database_url="postgresql://user:pass@localhost/smarthunt",
            redis_url="redis://localhost:6379",
            secret_key="test-secret-key-32-characters-long-key-32-characters-long",
            jwt_secret_key="test-jwt-secret-key-with-more-than-32-characters-long-safe-safe",
            app_env="production",
            app_debug=True,
        )
