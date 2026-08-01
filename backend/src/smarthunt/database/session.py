from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from smarthunt.core.config import settings

_engine_kwargs = {"echo": False, "pool_pre_ping": True, "future": True}
if settings.app_env == "test":
    # pytest-asyncio gives each test function its own event loop; a pooled
    # connection created in one test's loop is unusable in the next and
    # blows up with "Event loop is closed" on cleanup. NullPool opens a
    # fresh connection per checkout instead of reusing across loops —
    # matches what tests/conftest.py's own separate engine already does.
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def close_engine() -> None:
    await engine.dispose()
