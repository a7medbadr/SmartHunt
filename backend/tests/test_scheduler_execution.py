import pytest

from smarthunt.scheduler.execution import (
    execute_scheduler_job,
)


@pytest.mark.asyncio
async def test_execution_module_exists():

    assert execute_scheduler_job is not None
