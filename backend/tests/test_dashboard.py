from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from fastapi import status

from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job


@pytest.mark.asyncio
async def test_get_dashboard_statistics_empty_db(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/statistics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "jobs" in data
    assert "applications" in data
    assert "favorites" in data
    assert "linkedin_posts" in data
    assert "whatsapp_posts" in data
    assert "job_sites" in data
    assert "not_suitable_jobs" in data
    assert "providers" in data
    assert isinstance(data["jobs"], int)


@pytest.mark.asyncio
async def test_dashboard_statistics_reflects_real_data(client: AsyncClient, db_session):
    before = (await client.get("/api/v1/dashboard/statistics")).json()

    db_session.add(
        Job(
            title="Dashboard Stats Test Job",
            company="Acme",
            location="Remote",
            source="linkedin",
            url="https://example.com/jobs/dashboard-stats-test",
        )
    )
    db_session.add(
        Job(
            title="Dashboard Stats LinkedIn Post Job",
            company="LinkedIn Post",
            location="Saudi Arabia",
            source="linkedin_post",
            url="https://example.com/jobs/dashboard-stats-post-test",
            post_url="https://www.linkedin.com/feed/#dashboard-stats-test",
        )
    )
    db_session.add(
        Job(
            title="Dashboard Stats WhatsApp Message Job",
            company="WhatsApp Channel",
            location="Saudi Arabia",
            source="whatsapp_message",
            url="https://whatsapp.com/channel/dashboard-stats-test#msg-1",
            post_url="https://whatsapp.com/channel/dashboard-stats-test#msg-1",
        )
    )
    await db_session.commit()

    after = (await client.get("/api/v1/dashboard/statistics")).json()

    assert after["jobs"] == before["jobs"] + 3
    assert after["linkedin_posts"] == before["linkedin_posts"] + 1
    assert after["whatsapp_posts"] == before["whatsapp_posts"] + 1
    assert after["job_sites"] == before["job_sites"] + 1
    assert after["providers"] > 0


@pytest.mark.asyncio
async def test_dashboard_counts_exclude_already_reviewed_jobs(client: AsyncClient, db_session):
    # Regression: the linkedin_posts/job_sites/whatsapp_posts cards used to
    # count every job ever discovered with that source regardless of
    # review_status, so the dashboard showed "61" for LinkedIn posts while
    # the actual /jobs/linkedin tab (which only shows review_status IS
    # NULL rows) showed 4 — found live 2026-08-12. A job already marked
    # applied/not_suitable must not inflate these counts, and a
    # not_suitable one must show up in not_suitable_jobs instead.
    before = (await client.get("/api/v1/dashboard/statistics")).json()

    db_session.add(
        Job(
            title="Reviewed LinkedIn Post Job",
            company="LinkedIn Post",
            location="Saudi Arabia",
            source="linkedin_post",
            url="https://example.com/jobs/reviewed-post-test",
            post_url="https://www.linkedin.com/feed/#reviewed-post-test",
            review_status="applied",
        )
    )
    db_session.add(
        Job(
            title="Not Suitable LinkedIn Post Job",
            company="LinkedIn Post",
            location="Saudi Arabia",
            source="linkedin_post",
            url="https://example.com/jobs/not-suitable-post-test",
            post_url="https://www.linkedin.com/feed/#not-suitable-post-test",
            review_status="not_suitable",
        )
    )
    await db_session.commit()

    after = (await client.get("/api/v1/dashboard/statistics")).json()

    assert after["linkedin_posts"] == before["linkedin_posts"]
    assert after["not_suitable_jobs"] == before["not_suitable_jobs"] + 1


@pytest.mark.asyncio
async def test_get_dashboard_timeseries_default_range(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/timeseries")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["points"]) == 14
    today = data["points"][-1]
    for key in ("date", "job_sites", "linkedin_posts", "whatsapp_posts", "applications"):
        assert key in today


@pytest.mark.asyncio
async def test_dashboard_timeseries_reflects_todays_activity(client: AsyncClient, db_session):
    before = (await client.get("/api/v1/dashboard/timeseries?days=7")).json()
    before_today = before["points"][-1]

    db_session.add(
        Job(
            title="Timeseries Test Job Site",
            company="Acme",
            location="Riyadh, Saudi Arabia",
            source="linkedin",
            url="https://example.com/jobs/timeseries-site-test",
        )
    )
    db_session.add(
        Job(
            title="Timeseries Test LinkedIn Post",
            company="LinkedIn Post",
            location="Saudi Arabia",
            source="linkedin_post",
            url="https://example.com/jobs/timeseries-post-test",
            post_url="https://www.linkedin.com/feed/#timeseries-test",
        )
    )
    db_session.add(
        Application(
            job_title="Timeseries Test Application",
            company="Acme",
            status="APPLIED",
            created_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    after = (await client.get("/api/v1/dashboard/timeseries?days=7")).json()
    after_today = after["points"][-1]

    assert after_today["date"] == before_today["date"]
    assert after_today["job_sites"] == before_today["job_sites"] + 1
    assert after_today["linkedin_posts"] == before_today["linkedin_posts"] + 1
    assert after_today["applications"] == before_today["applications"] + 1
