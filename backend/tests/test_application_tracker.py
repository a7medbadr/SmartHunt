import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_application_tracker_flow(client: AsyncClient) -> None:
    # Try endpoint without trailing slash to avoid 307 redirect
    res = await client.get("/api/v1/applications", follow_redirects=True)
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_not_found_handling(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Update non-existing
    update_res = await client.patch(
        f"/api/v1/applications/{fake_id}", json={"status": "Offer"}
    )
    assert update_res.status_code in (404, 422)

    # Delete non-existing
    delete_res = await client.delete(f"/api/v1/applications/{fake_id}")
    assert delete_res.status_code in (404, 422)
