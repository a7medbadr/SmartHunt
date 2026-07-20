import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_scheduler_locks_empty(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/scheduler/locks"
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_scheduler_locks_endpoint(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/scheduler/locks"
    )

    assert response.status_code == 200
    assert isinstance(
        response.json(),
        list,
    )
