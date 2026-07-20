import pytest
import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session):
    yield


@pytest.mark.asyncio
async def test_valid_resume(client):
    response = await client.post(
        "/api/v1/resume/profile",
        json={
            "resume": "John Doe\nEmail: john@example.com\nPhone:+966501234567\n8 years of experience\nPython Linux"
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_empty_resume(client):
    response = await client.post(
        "/api/v1/resume/profile",
        json={"resume": ""},
    )

    assert response.status_code == 200
    assert response.json()["email"] is None


@pytest.mark.asyncio
async def test_invalid_body(client):
    response = await client.post(
        "/api/v1/resume/profile",
        json=[],
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_resume_field(client):
    response = await client.post(
        "/api/v1/resume/profile",
        json={},
    )

    assert response.status_code == 422
