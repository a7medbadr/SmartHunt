import uuid

import pytest

from smarthunt.database.models.job import Job


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


@pytest.mark.asyncio
async def test_get_job_by_id(client):
    token = await create_user(client)

    created = await client.post(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Platform Engineer",
            "company": "Acme",
            "location": "Remote",
            "source": "Manual",
            "url": f"https://example.com/{uuid.uuid4()}",
        },
    )
    job_id = created.json()["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["title"] == "Platform Engineer"


@pytest.mark.asyncio
async def test_get_job_by_id_not_found(client):
    response = await client.get("/api/v1/jobs/999999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_job_response_surfaces_no_sponsorship_signal(client, db_session):
    job = Job(
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        source="test",
        url=f"https://example.com/{uuid.uuid4()}",
        description="Note: we are unable to sponsor visas for this role.",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/v1/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json()["no_sponsorship_signal"] is True
