from contextlib import asynccontextmanager
from smarthunt.database.session import create_engine, close_engine


@asynccontextmanager
async def lifespan(app):
    await create_engine()
    yield
    await close_engine()
