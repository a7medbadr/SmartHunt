import asyncio
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded before engine initialization
load_dotenv()

from smarthunt.database.session import engine
from smarthunt.database.base import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    if engine is None:
        raise RuntimeError("Database engine is not initialized. Please check your DATABASE_URL environment variable.")
    
    logger.info("Creating all missing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
