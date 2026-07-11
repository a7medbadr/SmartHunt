from sqlalchemy import text

from smarthunt.database.session import engine


async def check_database_connection() -> bool:
    """Check database connectivity."""

    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
        return True

    except Exception:
        return False
