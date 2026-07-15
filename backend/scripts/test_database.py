import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# قراءة الـ DATABASE_URL مع إمكانية التبديل لـ localhost محلياً كـ fallback ذكي
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/smarthunt"
)


async def test_connection():
    print(f"Connecting to database using: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # اختبار اتصال بسيط جداً وآمن
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1"))
            print(f"Database connection successful! Result: {result.scalar()}")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
