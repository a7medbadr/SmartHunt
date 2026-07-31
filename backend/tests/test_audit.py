from datetime import datetime, timedelta, timezone

from httpx import AsyncClient


async def test_create_and_get_audit_logs(client: AsyncClient):

    response = await client.get("/api/v1/audit/logs")

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )


async def test_audit_filter_action(client: AsyncClient):

    response = await client.get(
        "/api/v1/audit/logs",
        params={"action": "LOGIN"},
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )


async def test_audit_filter_resource_type(client: AsyncClient):

    response = await client.get(
        "/api/v1/audit/logs",
        params={"resource_type": "application"},
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )


async def test_audit_pagination(client: AsyncClient):

    response = await client.get(
        "/api/v1/audit/logs",
        params={
            "skip": 0,
            "limit": 10,
        },
    )

    assert response.status_code == 200

    assert len(response.json()) <= 10


async def test_audit_date_filters(client: AsyncClient):

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    response = await client.get(
        "/api/v1/audit/logs",
        params={
            "date_from": (now - timedelta(days=1)).isoformat(),
            "date_to": now.isoformat(),
        },
    )

    assert response.status_code == 200
