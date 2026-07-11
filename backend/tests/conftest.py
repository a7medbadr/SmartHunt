import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# تأكد أن هذا هو المسار الصحيح لاستيراد get_db في مشروعك
from smarthunt.database.session import get_db
from smarthunt.main import app

# رابط قاعدة بيانات الاختبار
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/smarthunt"


@pytest.fixture(scope="session")
def event_loop():
    """
    إنشاء Loop واحد فقط مشترك لجميع اختبارات الـ session بالكامل.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine(event_loop):
    """
    إنشاء الـ engine باستخدام الـ event_loop المشترك وتمرير NullPool.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def db_session(db_engine):
    """
    إنشاء جلسة قاعدة بيانات موحدة على مستوى الـ session متوافقة مع الـ Loop المشترك.
    """
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="session")
async def client(db_session):
    """
    إنشاء الـ client وحقن الـ db_session بداخل الـ overrides لـ FastAPI بنطاق session.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
