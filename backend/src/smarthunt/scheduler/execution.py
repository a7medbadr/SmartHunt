from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def execute_scheduler_job(
    handler: Callable[[], Awaitable[Any]],
) -> Any:
    return await handler()


async def track_scheduler_execution(
    handler: Callable[[], Awaitable[Any]],
) -> dict[str, Any]:

    started = _utc_now()

    try:
        result = await handler()

        finished = _utc_now()

        return {
            "status": "SUCCESS",
            "started_at": started,
            "finished_at": finished,
            "result": result,
        }

    except Exception as exc:

        finished = _utc_now()

        return {
            "status": "FAILED",
            "started_at": started,
            "finished_at": finished,
            "error": str(exc),
        }
