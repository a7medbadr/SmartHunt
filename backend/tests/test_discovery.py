import pytest

from smarthunt.discovery.service import DiscoveryService
from smarthunt.domain.job import DiscoveredJob
from smarthunt.providers import registry as provider_registry_module
from smarthunt.providers.settings import service as provider_settings_module


@pytest.mark.asyncio
async def test_discover_lets_remote_jobs_through_a_physical_location_filter(
    db_session, monkeypatch
):
    """Regression test: baaeed (and any future remote-only provider)
    returns location="Remote" for every job, which used to be silently
    excluded by every Saudi-Arabia-only scheduled run's location filter
    ("saudi arabia" not in "remote") — found 2026-08-03 while
    investigating why baaeed had produced zero real jobs despite being
    marked real_discovery=True. A job explicitly marked Remote must
    always pass the location filter, regardless of what location was
    searched for."""

    jobs = [
        DiscoveredJob(
            title="Linux Administrator",
            company="Acme",
            location="Remote",
            source="baaeed",
            url="https://baaeed.com/jobs/1",
        ),
        DiscoveredJob(
            title="Linux Administrator",
            company="Acme Riyadh",
            location="Riyadh, Saudi Arabia",
            source="sabbar",
            url="https://sabbar.com/jobs/2",
        ),
        DiscoveredJob(
            title="Linux Administrator",
            company="Acme Cairo",
            location="Cairo, Egypt",
            source="sabbar",
            url="https://sabbar.com/jobs/3",
        ),
    ]

    async def fake_fetch_all_jobs(self, **kwargs):
        return jobs

    async def fake_get_enabled_map(self, session):
        return {}

    # Patch the CLASS, not the `provider_registry`/`provider_settings_service`
    # singleton instances — those live for the whole test process, and
    # monkeypatch restoring an instance-level patch back to a
    # class-resolved bound method actually *stamps* that bound method onto
    # the instance permanently, silently shadowing any later test's own
    # class-level monkeypatch of the same method for the rest of the run.
    monkeypatch.setattr(
        provider_registry_module.ProviderRegistry, "fetch_all_jobs", fake_fetch_all_jobs
    )
    monkeypatch.setattr(
        provider_settings_module.ProviderSettingsService,
        "get_enabled_map",
        fake_get_enabled_map,
    )

    result = await DiscoveryService(db_session).discover(query="linux", location="Saudi Arabia")

    # Remote + the real Saudi Arabia match pass; the Egypt-located one
    # doesn't.
    assert result["discovered"] == 2


@pytest.mark.asyncio
async def test_discover_can_restrict_to_specific_providers(db_session, monkeypatch):
    """discover_tanqeeb_daily (scheduler/jobs.py) needs discover() to run
    the exact same filtered/scored/saved pipeline every other scheduled
    discovery job gets, just restricted to one named provider instead of
    every enabled one — added 2026-08-07. Confirms the `providers` kwarg
    actually narrows which providers fetch_all_jobs is called with,
    intersected with enabled/disabled rather than bypassing it."""
    captured: dict = {}

    async def fake_fetch_all_jobs(self, **kwargs):
        captured["providers"] = kwargs.get("providers")
        return []

    async def fake_get_enabled_map(self, session):
        return {}

    monkeypatch.setattr(
        provider_registry_module.ProviderRegistry, "fetch_all_jobs", fake_fetch_all_jobs
    )
    monkeypatch.setattr(
        provider_settings_module.ProviderSettingsService,
        "get_enabled_map",
        fake_get_enabled_map,
    )

    await DiscoveryService(db_session).discover(
        query="linux", location="Saudi Arabia", providers=["tanqeeb"]
    )

    assert captured["providers"] is not None
    assert [p.name for p in captured["providers"]] == ["tanqeeb"]


@pytest.mark.asyncio
async def test_search_single_provider_only_calls_the_named_provider(db_session, monkeypatch):
    """ "Search this specific site" (2026-08-04) must actually search only
    that one site, not fall back to the local jobs table, and must not
    force the Saudi-only location filter discover() uses — the owner
    typed this specific location (or none) for this specific search and
    that should be respected as-is."""
    # Title/company deliberately distinct from other tests' generic
    # "Linux Administrator"/"Acme" fixtures — JobRepository's cross-source
    # dedup (2026-08-13) now matches on normalized title+company across
    # the *entire* jobs table, not just same-source, so reusing that
    # generic pair here would collide with another test's own
    # directly-committed row (see the comment below) and get silently
    # skipped as a "duplicate" instead of actually inserted.
    jobs = [
        DiscoveredJob(
            title="Linux Administrator (Single-Provider Test Fixture)",
            company="Acme Single-Provider Test Fixture Co",
            location="Cairo, Egypt",  # would fail a Saudi-only location filter
            source="linkedin",
            url="https://linkedin.com/jobs/1",
        ),
    ]

    called_with_providers = []

    async def fake_fetch_all_jobs(self, providers=None, **kwargs):
        called_with_providers.extend(p.name for p in (providers or []))
        return jobs

    async def fake_get_enabled_map(self, session):
        return {}

    monkeypatch.setattr(
        provider_registry_module.ProviderRegistry, "fetch_all_jobs", fake_fetch_all_jobs
    )
    monkeypatch.setattr(
        provider_settings_module.ProviderSettingsService,
        "get_enabled_map",
        fake_get_enabled_map,
    )

    # save_discovered_jobs() commits directly (see job_repository.py), so
    # unlike most fixtures here db_session's rollback-on-teardown doesn't
    # undo this insert — a fixed URL would only ever insert once across
    # this whole test DB's lifetime and fail as a "duplicate" on every
    # later run. Delete any leftover row from a prior run first so this
    # test is idempotent.
    from sqlalchemy import delete

    from smarthunt.database.models.job import Job

    await db_session.execute(delete(Job).where(Job.url == "https://linkedin.com/jobs/1"))
    await db_session.commit()

    result = await DiscoveryService(db_session).search_single_provider(
        provider_name="linkedin", query="anything", location="Saudi Arabia"
    )

    assert called_with_providers == ["linkedin"]
    assert result["found"] == 1
    assert result["inserted"] == 1


@pytest.mark.asyncio
async def test_search_single_provider_still_filters_irrelevant_titles(db_session, monkeypatch):
    """Regression test: an early version of search_single_provider
    deliberately skipped the title-relevance filter on the theory that
    the owner picked this site/query and should see raw results — found
    live 2026-08-04 that this let LinkedIn's own semantically-broadened
    results (QA testers, product managers, etc. for a "Linux
    Administrator" query) land in the shared jobs list with inflated
    scores, exactly the "jobs with no relation to my work" clutter the
    owner asked to have removed. Must filter the same as discover()."""
    jobs = [
        DiscoveredJob(
            title="Product Manager - Desktop",
            company="Acme",
            location="Saudi Arabia",
            source="linkedin",
            url="https://linkedin.com/jobs/irrelevant-1",
        ),
    ]

    async def fake_fetch_all_jobs(self, providers=None, **kwargs):
        return jobs

    async def fake_get_enabled_map(self, session):
        return {}

    monkeypatch.setattr(
        provider_registry_module.ProviderRegistry, "fetch_all_jobs", fake_fetch_all_jobs
    )
    monkeypatch.setattr(
        provider_settings_module.ProviderSettingsService,
        "get_enabled_map",
        fake_get_enabled_map,
    )

    result = await DiscoveryService(db_session).search_single_provider(
        provider_name="linkedin", query="linux"
    )

    assert result["found"] == 0
    assert result["inserted"] == 0


@pytest.mark.asyncio
async def test_search_single_provider_rejects_unknown_provider(db_session):
    with pytest.raises(ValueError):
        await DiscoveryService(db_session).search_single_provider(
            provider_name="not-a-real-provider", query="anything"
        )


@pytest.mark.asyncio
async def test_search_single_provider_rejects_disabled_provider(db_session, monkeypatch):
    async def fake_get_enabled_map(self, session):
        return {"linkedin": False}

    monkeypatch.setattr(
        provider_settings_module.ProviderSettingsService,
        "get_enabled_map",
        fake_get_enabled_map,
    )

    with pytest.raises(ValueError):
        await DiscoveryService(db_session).search_single_provider(
            provider_name="linkedin", query="anything"
        )


@pytest.mark.asyncio
async def test_search_provider_endpoint_returns_400_for_unknown_provider(client):
    response = await client.post(
        "/api/v1/discovery/search-provider",
        params={"provider": "not-a-real-provider", "query": "anything"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_discovery_run_does_not_crash(client):
    """Regression test: several providers didn't accept the page/limit
    kwargs ProviderRegistry.fetch_all_jobs always passes, and three more
    returned a dict instead of a list of jobs — both crashed the endpoint
    with an unhandled 500 instead of gracefully degrading per provider."""
    response = await client.post(
        "/api/v1/discovery/run",
        params={"query": "engineer", "location": "remote"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["providers"] == 14
    assert data["discovered"] >= 0
    assert data["inserted"] >= 0


@pytest.mark.asyncio
async def test_discovery_run_records_scheduler_history(client):
    before = await client.get("/api/v1/scheduler/history")
    before_count = len(before.json())

    response = await client.post(
        "/api/v1/discovery/run",
        params={"query": "engineer"},
    )
    assert response.status_code == 200

    after = await client.get("/api/v1/scheduler/history")
    after_count = len(after.json())

    assert after_count == before_count + 1
    assert after.json()[0]["provider"] == "manual-run"
