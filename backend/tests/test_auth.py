import uuid

import pytest


def random_user():
    uid = uuid.uuid4().hex[:8]

    return {
        "username": f"user_{uid}",
        "email": f"{uid}@example.com",
        "password": "Secret123",
    }


@pytest.mark.asyncio
async def test_register(client):
    payload = random_user()

    response = await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["username"] == payload["username"]


@pytest.mark.asyncio
async def test_login(client):
    payload = random_user()

    await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 200

    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_me(client):
    payload = random_user()

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

    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    assert response.json()["username"] == payload["username"]


@pytest.mark.asyncio
async def test_protected_endpoint_requires_login(client):
    response = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Test",
            "company": "IBM",
            "location": "Remote",
            "source": "Manual",
            "url": "https://example.com/test",
        },
    )

    assert response.status_code == 401
