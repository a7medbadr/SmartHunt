import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.saved_searches.models import SavedSearch


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(SavedSearch))
    await db_session.commit()

    yield

    await db_session.execute(delete(SavedSearch))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_saved_search(client: AsyncClient):
    response = await client.post(
        "/api/v1/saved-searches",
        json={"name": "Linux Saudi", "keyword": "linux", "location": "Saudi Arabia"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Linux Saudi"
    assert data["keyword"] == "linux"
    assert data["location"] == "Saudi Arabia"


@pytest.mark.asyncio
async def test_list_saved_searches(client: AsyncClient):
    await client.post("/api/v1/saved-searches", json={"name": "Search 1", "keyword": "python"})
    await client.post("/api/v1/saved-searches", json={"name": "Search 2", "keyword": "devops"})

    response = await client.get("/api/v1/saved-searches")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_saved_search(client: AsyncClient):
    response = await client.post(
        "/api/v1/saved-searches", json={"name": "To Delete", "keyword": "docker"}
    )
    search_id = response.json()["id"]

    response = await client.delete(f"/api/v1/saved-searches/{search_id}")
    assert response.status_code == 204

    response = await client.get("/api/v1/saved-searches")
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_saved_search(client: AsyncClient):
    response = await client.delete("/api/v1/saved-searches/999999")
    assert response.status_code == 404
