from collections.abc import Awaitable, Callable
from typing import Any


async def execute_scheduler_job(
    handler: Callable[[], Awaitable[Any]],
) -> Any:
    return await handler()
