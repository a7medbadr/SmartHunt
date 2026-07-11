import uuid

import pytest


async def create_user(client):
    uid = uuid.uuid4().hex[:8]

    payload = {
        "username": f"user_{uid}",
        "email": f"{uid}@example.com",
        "password": "Secret123",
    }

    await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
        },
    )

    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_create_job(client):
    token = await create_user(client)

    response = await client.post(
        "/api/v1/jobs",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "DevOps Engineer",
            "company": "IBM",
            "location": "Remote",
            "source": "Manual",
            "url": f"https://example.com/{uuid.uuid4()}",
        },
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_jobs(client):
    token = await create_user(client)

    response = await client.get(
        "/api/v1/jobs",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    assert isinstance(response.json(), list)
