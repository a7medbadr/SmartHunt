import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

TEST_DB = os.getenv("TEST_DB_NAME", "smarthunt_test")


async def main():
    engine = create_async_engine(
        DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.begin() as conn:
        exists = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname=:name"),
            {"name": TEST_DB},
        )

        if exists.scalar() is None:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
