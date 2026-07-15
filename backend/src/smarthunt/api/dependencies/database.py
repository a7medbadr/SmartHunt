from smarthunt.database import session as db_session


async def get_db():
    if db_session.AsyncSessionLocal is None:
        raise RuntimeError(
            "Database session maker is not initialized. Ensure lifespan has run."
        )
    async with db_session.AsyncSessionLocal() as session:
        yield session
