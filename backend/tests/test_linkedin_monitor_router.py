from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.linkedin_monitor import router as router_module
from smarthunt.linkedin_monitor.models import MonitoredHashtag, MonitoredLinkedInAccount
from smarthunt.linkedin_monitor.post_scanner import LinkedInScanError


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "linkedin_post"))
    await db_session.execute(delete(MonitoredLinkedInAccount))
    await db_session.execute(delete(MonitoredHashtag))
    await db_session.commit()


@pytest.mark.asyncio
async def test_add_and_list_account(client: AsyncClient):
    response = await client.post(
        "/api/v1/linkedin-monitor/accounts",
        json={"profile_url": "https://linkedin.com/in/someone", "label": "HR lead"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["profile_url"] == "https://linkedin.com/in/someone"
    assert data["enabled"] is True

    list_response = await client.get("/api/v1/linkedin-monitor/accounts")
    assert list_response.status_code == 200
    assert any(a["id"] == data["id"] for a in list_response.json())


@pytest.mark.asyncio
async def test_update_and_delete_account(client: AsyncClient):
    create = await client.post(
        "/api/v1/linkedin-monitor/accounts",
        json={"profile_url": "https://linkedin.com/in/someone-else"},
    )
    account_id = create.json()["id"]

    update = await client.patch(
        f"/api/v1/linkedin-monitor/accounts/{account_id}", json={"enabled": False}
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete_response = await client.delete(f"/api/v1/linkedin-monitor/accounts/{account_id}")
    assert delete_response.status_code == 204

    missing_update = await client.patch(
        f"/api/v1/linkedin-monitor/accounts/{account_id}", json={"enabled": True}
    )
    assert missing_update.status_code == 404


@pytest.mark.asyncio
async def test_scan_account_saves_relevant_posts_and_marks_checked(
    client: AsyncClient, monkeypatch
):
    create = await client.post(
        "/api/v1/linkedin-monitor/accounts",
        json={"profile_url": "https://linkedin.com/in/hr-person"},
    )
    account_id = create.json()["id"]

    fake_posts = [
        {
            "urn": "urn:li:activity:9999",
            "text": (
                "We're hiring a Linux Administrator in Riyadh, Saudi Arabia. "
                "Send your CV to apply now."
            ),
            "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:9999/",
        }
    ]

    monkeypatch.setattr(router_module, "scan_profile_posts", AsyncMock(return_value=fake_posts))

    response = await client.post(f"/api/v1/linkedin-monitor/accounts/{account_id}/scan")

    assert response.status_code == 200
    data = response.json()
    assert data["scanned"] == 1
    assert data["saved"] == 1
    assert len(data["job_ids"]) == 1

    accounts = await client.get("/api/v1/linkedin-monitor/accounts")
    updated = next(a for a in accounts.json() if a["id"] == account_id)
    assert updated["last_checked_at"] is not None


@pytest.mark.asyncio
async def test_scan_account_requires_existing_account(client: AsyncClient):
    response = await client.post("/api/v1/linkedin-monitor/accounts/999999/scan")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_scan_feed_saves_relevant_posts(client: AsyncClient, monkeypatch):
    fake_posts = [
        {
            "urn": "urn:li:activity:8888",
            "text": "Just had lunch with the team!",
            "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:8888/",
        }
    ]
    monkeypatch.setattr(router_module, "scan_home_feed", AsyncMock(return_value=fake_posts))

    response = await client.post("/api/v1/linkedin-monitor/scan-feed")

    assert response.status_code == 200
    data = response.json()
    assert data["scanned"] == 1
    assert data["saved"] == 0


"""Hashtag CRUD tests: added 2026-08-06 — hashtags moved from a hardcoded
Python list to a real, owner-editable DB table (mirrors the account
tests above exactly)."""


@pytest.mark.asyncio
async def test_add_and_list_hashtag(client: AsyncClient):
    response = await client.post("/api/v1/linkedin-monitor/hashtags", json={"tag": "Hiring"})
    assert response.status_code == 201
    data = response.json()
    assert data["tag"] == "Hiring"
    assert data["enabled"] is True

    list_response = await client.get("/api/v1/linkedin-monitor/hashtags")
    assert list_response.status_code == 200
    assert any(h["id"] == data["id"] for h in list_response.json())


@pytest.mark.asyncio
async def test_add_hashtag_strips_leading_hash(client: AsyncClient):
    response = await client.post("/api/v1/linkedin-monitor/hashtags", json={"tag": "#DevOps"})
    assert response.status_code == 201
    assert response.json()["tag"] == "DevOps"


@pytest.mark.asyncio
async def test_update_and_delete_hashtag(client: AsyncClient):
    create = await client.post("/api/v1/linkedin-monitor/hashtags", json={"tag": "Linux"})
    hashtag_id = create.json()["id"]

    update = await client.patch(
        f"/api/v1/linkedin-monitor/hashtags/{hashtag_id}", json={"enabled": False}
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete_response = await client.delete(f"/api/v1/linkedin-monitor/hashtags/{hashtag_id}")
    assert delete_response.status_code == 204

    missing_update = await client.patch(
        f"/api/v1/linkedin-monitor/hashtags/{hashtag_id}", json={"enabled": True}
    )
    assert missing_update.status_code == 404


@pytest.mark.asyncio
async def test_scan_hashtag_saves_relevant_posts_and_marks_checked(
    client: AsyncClient, monkeypatch
):
    create = await client.post("/api/v1/linkedin-monitor/hashtags", json={"tag": "Hiring"})
    hashtag_id = create.json()["id"]

    fake_posts = [
        {
            "urn": "urn:li:activity:7777",
            "text": (
                "We're hiring a Linux Administrator in Riyadh, Saudi Arabia. "
                "Send your CV to apply now."
            ),
            "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7777/",
        }
    ]
    monkeypatch.setattr(router_module, "scan_hashtag_posts", AsyncMock(return_value=fake_posts))

    response = await client.post(f"/api/v1/linkedin-monitor/hashtags/{hashtag_id}/scan")

    assert response.status_code == 200
    data = response.json()
    assert data["scanned"] == 1
    assert data["saved"] == 1

    hashtags = await client.get("/api/v1/linkedin-monitor/hashtags")
    updated = next(h for h in hashtags.json() if h["id"] == hashtag_id)
    assert updated["last_checked_at"] is not None


@pytest.mark.asyncio
async def test_scan_hashtag_requires_existing_hashtag(client: AsyncClient):
    response = await client.post("/api/v1/linkedin-monitor/hashtags/999999/scan")
    assert response.status_code == 404


"""Scan-failure-reason regression tests: added 2026-08-06 per explicit
request — a failed scan must surface a specific reason (connection
issue? browser down? session busy?) through the API, not just a generic
500 that the frontend renders as the same "حصل خطأ، جرب تاني" every
time."""


@pytest.mark.asyncio
async def test_scan_feed_surfaces_specific_error_reason(client: AsyncClient, monkeypatch):
    async def fake_scan_home_feed():
        raise LinkedInScanError("مشكلة في الاتصال مع لينكدان — الصفحة أخدت وقت طويل من غير رد.")

    monkeypatch.setattr(router_module, "scan_home_feed", fake_scan_home_feed)

    response = await client.post("/api/v1/linkedin-monitor/scan-feed")

    assert response.status_code == 502
    assert "الاتصال" in response.json()["message"]


@pytest.mark.asyncio
async def test_scan_account_surfaces_specific_error_reason(client: AsyncClient, monkeypatch):
    create = await client.post(
        "/api/v1/linkedin-monitor/accounts",
        json={"profile_url": "https://linkedin.com/in/error-test"},
    )
    account_id = create.json()["id"]

    async def fake_scan_profile_posts(profile_url):
        raise LinkedInScanError("المتصفح مش قادر يشتغل دلوقتي — جرب تاني بعد شوية.")

    monkeypatch.setattr(router_module, "scan_profile_posts", fake_scan_profile_posts)

    response = await client.post(f"/api/v1/linkedin-monitor/accounts/{account_id}/scan")

    assert response.status_code == 502
    assert "المتصفح" in response.json()["message"]


@pytest.mark.asyncio
async def test_scan_hashtag_surfaces_specific_error_reason(client: AsyncClient, monkeypatch):
    create = await client.post("/api/v1/linkedin-monitor/hashtags", json={"tag": "ErrorTest"})
    hashtag_id = create.json()["id"]

    async def fake_scan_hashtag_posts(hashtag):
        raise LinkedInScanError("فيه فحص تاني شغال دلوقتي على نفس السيشن — استنى شوية وجرب تاني.")

    monkeypatch.setattr(router_module, "scan_hashtag_posts", fake_scan_hashtag_posts)

    response = await client.post(f"/api/v1/linkedin-monitor/hashtags/{hashtag_id}/scan")

    assert response.status_code == 502
    assert "فحص تاني" in response.json()["message"]
