from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from smarthunt.core.config import settings

engine = None
AsyncSessionLocal = None


async def create_engine():
    global engine, AsyncSessionLocal

    engine = create_async_engine(
        settings.database_url,
        echo=settings.app_debug,
        future=True,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def close_engine():
    global engine
    if engine:
        await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
