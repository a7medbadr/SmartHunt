from sqlalchemy import text

from smarthunt.database.session import engine


async def check_database_health() -> bool:
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

        return result.scalar() == 1
