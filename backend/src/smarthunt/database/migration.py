import os
import subprocess
from pathlib import Path

import structlog

logger = structlog.get_logger()


async def run_migrations() -> None:
    backend_path = Path(__file__).resolve().parents[3]

    env = os.environ.copy()

    result = subprocess.run(
        [
            "alembic",
            "upgrade",
            "head",
        ],
        cwd=backend_path,
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(
            "alembic_failed",
            stdout=result.stdout,
            stderr=result.stderr,
        )
        raise RuntimeError("Alembic migration failed")

    logger.info(
        "alembic_completed",
        output=result.stdout,
    )
