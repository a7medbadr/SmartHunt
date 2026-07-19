from contextlib import asynccontextmanager

from fastapi import FastAPI

from smarthunt.core.logging import setup_logging
from smarthunt.database.health import check_database_health
from smarthunt.database.migration import run_migrations
from smarthunt.database.session import close_engine

import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger.info("application_startup")

    try:
        await run_migrations()
        logger.info("database_migration_completed")
    except Exception:
        logger.exception("database_migration_failed")
        raise

    try:
        await check_database_health()
        logger.info("database_health_check_passed")
    except Exception:
        logger.exception("database_health_check_failed")
        raise

    yield

    logger.info("application_shutdown")

    await close_engine()

    logger.info("database_connection_closed")
