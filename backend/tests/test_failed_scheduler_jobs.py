import pytest

from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)


@pytest.mark.asyncio
async def test_failed_scheduler_service_exists():

    assert failed_scheduler_job_service is not None
