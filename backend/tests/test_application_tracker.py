from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from smarthunt.database.models.application import Application


@pytest.mark.asyncio
async def test_application_tracker_flow(client: AsyncClient) -> None:
    # Try endpoint without trailing slash to avoid 307 redirect
    res = await client.get("/api/v1/applications", follow_redirects=True)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_application_persists_in_real_database(client: AsyncClient, db_session) -> None:
    """Applications must be stored in the real applications table, not an
    in-memory list that's wiped on restart and invisible to other queries
    (e.g. the dashboard's application count)."""
    create_res = await client.post(
        "/api/v1/applications",
        json={
            "job_title": "Persistence Test Job",
            "company": "Acme",
            "status": "Applied",
        },
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    row = await db_session.get(Application, app_id)
    assert row is not None
    assert row.job_title == "Persistence Test Job"

    update_res = await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "Interviewing"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Interviewing"

    delete_res = await client.delete(f"/api/v1/applications/{app_id}")
    assert delete_res.status_code == 204

    assert await db_session.get(Application, app_id) is None


@pytest.mark.asyncio
async def test_needs_follow_up_flag(client: AsyncClient, db_session) -> None:
    """An application sitting in 'Applied' for a week+ with no status
    change should surface as needing a follow-up; a fresh one shouldn't."""
    create_res = await client.post(
        "/api/v1/applications",
        json={"job_title": "Follow-up Test Job", "company": "Acme", "status": "Applied"},
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]
    assert create_res.json()["needs_follow_up"] is False
    assert create_res.json()["days_since_applied"] == 0

    row = await db_session.get(Application, app_id)
    row.created_at = datetime.now(timezone.utc) - timedelta(days=10)
    await db_session.commit()

    list_res = await client.get("/api/v1/applications")
    application = next(a for a in list_res.json() if a["id"] == app_id)
    assert application["needs_follow_up"] is True
    assert application["days_since_applied"] >= 10


@pytest.mark.asyncio
async def test_not_found_handling(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Update non-existing
    update_res = await client.patch(f"/api/v1/applications/{fake_id}", json={"status": "Offer"})
    assert update_res.status_code in (404, 422)

    # Delete non-existing
    delete_res = await client.delete(f"/api/v1/applications/{fake_id}")
    assert delete_res.status_code in (404, 422)
