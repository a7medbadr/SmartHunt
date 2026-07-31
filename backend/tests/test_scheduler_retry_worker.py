import pytest

from smarthunt.scheduler.retry_worker import (
    scheduler_retry_worker,
)


@pytest.mark.asyncio
async def test_retry_worker_exists():

    assert scheduler_retry_worker is not None
