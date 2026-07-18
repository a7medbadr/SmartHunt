import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_application_lifecycle(client: AsyncClient) -> None:
    # 1. Create Application
    create_payload = {
        "job_title": "Linux Systems Administrator",
        "company": "Red Hat",
        "url": "https://jobs.redhat.com/123",
        "status": "Applied",
    }
    create_res = await client.post("/api/v1/applications", json=create_payload)
    assert create_res.status_code == 201
    app_data = create_res.json()

    app_id = app_data["id"]
    assert app_data["job_title"] == "Linux Systems Administrator"
    assert app_data["status"] == "Applied"

    # 2. Read Applications List
    list_res = await client.get("/api/v1/applications")
    assert list_res.status_code == 200
    apps = list_res.json()
    assert len(apps) > 0
    assert any(a["id"] == app_id for a in apps)

    # 3. Update Status
    update_res = await client.patch(
        f"/api/v1/applications/{app_id}", json={"status": "Technical Interview"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Technical Interview"

    # 4. Delete Application
    delete_res = await client.delete(f"/api/v1/applications/{app_id}")
    assert delete_res.status_code == 204

    # Verify Deletion
    list_after_delete = await client.get("/api/v1/applications")
    assert not any(a["id"] == app_id for a in list_after_delete.json())


@pytest.mark.asyncio
async def test_invalid_status(client: AsyncClient) -> None:
    create_payload = {
        "job_title": "DevOps Engineer",
        "company": "Canonical",
        "status": "InvalidStatusName",
    }
    res = await client.post("/api/v1/applications", json=create_payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_not_found_handling(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Update non-existing
    update_res = await client.patch(
        f"/api/v1/applications/{fake_id}", json={"status": "Offer"}
    )
    assert update_res.status_code == 404

    # Delete non-existing
    delete_res = await client.delete(f"/api/v1/applications/{fake_id}")
    assert delete_res.status_code == 404
