from contextlib import asynccontextmanager

from fastapi import FastAPI

from smarthunt.database.health import check_database_health
from smarthunt.database.migration import run_migrations
from smarthunt.database.session import close_engine
from smarthunt.logging.config import configure_logging

import structlog


logger = structlog.get_logger("smarthunt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    logger.info(
        "application_startup",
        service="smarthunt-backend",
    )

    try:
        await run_migrations()

        logger.info(
            "database_migration_completed",
            service="smarthunt-backend",
        )

    except Exception:
        logger.exception(
            "database_migration_failed",
            service="smarthunt-backend",
        )
        raise

    try:
        await check_database_health()

        logger.info(
            "database_health_check_passed",
            service="smarthunt-backend",
        )

    except Exception:
        logger.exception(
            "database_health_check_failed",
            service="smarthunt-backend",
        )
        raise

    yield

    logger.info(
        "application_shutdown",
        service="smarthunt-backend",
    )

    await close_engine()

    logger.info(
        "database_connection_closed",
        service="smarthunt-backend",
    )
