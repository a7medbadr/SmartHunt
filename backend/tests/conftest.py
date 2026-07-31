import os
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BACKEND_DIR / ".env.test",
    override=True,
)

os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-characters-long"
os.environ["SECRET_KEY"] = "test-secret-key-32-characters-long"

from smarthunt.api.dependencies import get_db
from smarthunt.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/smarthunt_test",
)


engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


TestSessionLocal = SessionLocal


@pytest.fixture(scope="session", autouse=True)
def migrate_database():
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
    )


@pytest_asyncio.fixture
async def db_session():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()

            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
