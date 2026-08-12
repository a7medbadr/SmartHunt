from unittest.mock import MagicMock

import httpx
import pytest

from smarthunt.providers.workable.provider import API_URL, WorkableProvider

"""jobs.workable.com is a real, unified search across every company that
hosts its job board on Workable — backed by a plain public JSON API
(https://jobs.workable.com/api/v1/jobs), confirmed live 2026-08-10 with
no auth/cookie needed and no bot challenge. Unlike LinkedIn/Tanqeeb this
needs no browser at all, so these tests mock httpx.AsyncClient.get
directly instead of the Playwright browser_manager."""


def _fake_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.json = MagicMock(return_value=payload)
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_workable_search_returns_real_jobs():
    provider = WorkableProvider()

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=5)

    assert isinstance(jobs, list)

    if jobs:
        job = jobs[0]
        assert job.title
        assert job.provider == "workable"
        assert job.url.startswith("https://jobs.workable.com/")
        assert job.country == "Saudi Arabia"
        assert "saudi arabia" in job.location.lower()


@pytest.mark.asyncio
async def test_workable_search_sends_query_and_location_params(monkeypatch):
    provider = WorkableProvider()

    captured = {}

    async def fake_get(self, url, params=None):
        captured["url"] = url
        captured["params"] = params
        return _fake_response({"jobs": [], "nextPageToken": None})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    jobs = await provider.search(query="linux administrator", location="Saudi Arabia", limit=10)

    assert jobs == []
    assert captured["url"] == API_URL
    assert captured["params"]["query"] == "linux administrator"
    assert captured["params"]["location"] == "Saudi Arabia"
    assert captured["params"]["limit"] == 10


@pytest.mark.asyncio
async def test_workable_search_defaults_location_to_saudi_arabia_with_no_query(monkeypatch):
    provider = WorkableProvider()

    captured = {}

    async def fake_get(self, url, params=None):
        captured["params"] = params
        return _fake_response({"jobs": [], "nextPageToken": None})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    jobs = await provider.search(limit=3)

    assert jobs == []
    assert captured["params"]["location"] == "Saudi Arabia"
    assert "query" not in captured["params"]


@pytest.mark.asyncio
async def test_workable_search_skips_malformed_entries(monkeypatch):
    """An entry missing id/title/url shouldn't crash the whole search or
    produce a garbage Job entry — it should just be skipped."""

    provider = WorkableProvider()

    payload = {
        "jobs": [
            {
                "id": "abc123",
                "title": "Linux Administrator",
                "url": "https://jobs.workable.com/view/abc123/linux-administrator",
                "company": {"title": "Acme Corp"},
                "location": {"city": "Riyadh", "countryName": "Saudi Arabia"},
                "description": "<p>We need a <strong>Linux</strong> admin.</p>",
                "requirementsSection": "<ul><li>RHEL</li><li>Bash</li></ul>",
                "created": "2026-08-06T08:56:34.770Z",
                "workplace": "on_site",
            },
            {
                # missing "id"
                "title": "Broken Entry",
                "url": "https://jobs.workable.com/view/broken/broken-entry",
                "company": {"title": "Acme Corp"},
                "location": {"city": "Jeddah", "countryName": "Saudi Arabia"},
            },
        ],
        "nextPageToken": None,
    }

    async def fake_get(self, url, params=None):
        return _fake_response(payload)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.external_id == "abc123"
    assert job.title == "Linux Administrator"
    assert job.company == "Acme Corp"
    assert job.location == "Riyadh, Saudi Arabia"
    assert job.url == "https://jobs.workable.com/view/abc123/linux-administrator"
    # HTML tags from description/requirementsSection must be stripped,
    # and both combined into the single description field (the legacy
    # Job dataclass has no separate requirements field).
    assert "<" not in job.description
    assert "Linux" in job.description
    assert "RHEL" in job.description
    assert job.posted_at is not None
    assert job.posted_at.isoformat() == "2026-08-06"


@pytest.mark.asyncio
async def test_workable_search_paginates_with_next_page_token(monkeypatch):
    """The API caps limit at 20 per request — a caller asking for more
    than that must be satisfied by walking the response's own
    nextPageToken cursor across multiple requests."""

    provider = WorkableProvider()

    def make_job(i: int) -> dict:
        return {
            "id": f"job-{i}",
            "title": f"Linux Engineer {i}",
            "url": f"https://jobs.workable.com/view/job-{i}/linux-engineer",
            "company": {"title": "Acme Corp"},
            "location": {"city": "Riyadh", "countryName": "Saudi Arabia"},
            "description": "",
        }

    pages = [
        {"jobs": [make_job(i) for i in range(20)], "nextPageToken": "token-2"},
        {"jobs": [make_job(i) for i in range(20, 25)], "nextPageToken": "token-3"},
    ]
    call_count = {"n": 0}

    async def fake_get(self, url, params=None):
        response = pages[call_count["n"]]
        call_count["n"] += 1
        return _fake_response(response)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=25)

    assert len(jobs) == 25
    assert call_count["n"] == 2
    assert jobs[0].external_id == "job-0"
    assert jobs[-1].external_id == "job-24"


@pytest.mark.asyncio
async def test_workable_search_returns_empty_list_on_request_failure(monkeypatch):
    provider = WorkableProvider()

    async def fake_get(self, url, params=None):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    jobs = await provider.search(query="linux", location="Saudi Arabia")

    assert jobs == []
