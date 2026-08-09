import pytest
from smarthunt.search.filtering import filter_jobs


@pytest.fixture
def sample_jobs():
    return [
        {
            "title": "Senior Linux System Administrator",
            "description": "Looking for RedHat and OpenShift expert",
            "location": "Riyadh",
            "source": "LinkedIn",
        },
        {
            "title": "Python Developer",
            "description": "FastAPI and PostgreSQL backend developer",
            "location": "Riyadh",
            "source": "Wuzzuf",
        },
        {
            "title": "DevOps Engineer",
            "description": "Linux, Docker, Kubernetes, CI/CD",
            "location": "Dubai",
            "source": "LinkedIn",
        },
        {
            "title": "Frontend Engineer",
            "description": "React and TypeScript specialist",
            "location": "Cairo",
            "source": "Indeed",
        },
    ]


def test_filter_by_keyword_title(sample_jobs):
    results = filter_jobs(sample_jobs, keyword="python")
    assert len(results) == 1
    assert results[0]["title"] == "Python Developer"


def test_filter_by_keyword_description(sample_jobs):
    results = filter_jobs(sample_jobs, keyword="linux")
    assert len(results) == 2
    titles = [j["title"] for j in results]
    assert "Senior Linux System Administrator" in titles
    assert "DevOps Engineer" in titles


def test_filter_by_location(sample_jobs):
    results = filter_jobs(sample_jobs, location="riyadh")
    assert len(results) == 2
    for job in results:
        assert job["location"].lower() == "riyadh"


def test_filter_by_source(sample_jobs):
    results = filter_jobs(sample_jobs, source="linkedin")
    assert len(results) == 2
    for job in results:
        assert job["source"].lower() == "linkedin"


def test_combined_filters(sample_jobs):
    results = filter_jobs(sample_jobs, keyword="linux", location="riyadh", source="linkedin")
    assert len(results) == 1
    assert results[0]["title"] == "Senior Linux System Administrator"


def test_no_results(sample_jobs):
    results = filter_jobs(sample_jobs, keyword="java", location="tokyo")
    assert len(results) == 0
    assert results == []


def test_filter_by_source_does_not_substring_match_a_longer_source():
    """Regression: source filtering used to be a substring match, so
    filtering by source="linkedin" also pulled in source="linkedin_post"
    rows (LinkedIn-post-sourced jobs), since "linkedin" is a substring of
    "linkedin_post" — found 2026-08-07 while building a separate tab for
    LinkedIn-post jobs. Must be an exact (case-insensitive) match."""
    jobs = [
        {"title": "Real LinkedIn search job", "source": "linkedin"},
        {"title": "LinkedIn post job", "source": "linkedin_post"},
    ]
    results = filter_jobs(jobs, source="linkedin")
    assert len(results) == 1
    assert results[0]["title"] == "Real LinkedIn search job"


def test_exclude_source_removes_only_the_exact_match(sample_jobs):
    jobs = sample_jobs + [{"title": "A post job", "source": "linkedin_post"}]
    results = filter_jobs(jobs, exclude_source="linkedin_post")
    assert all(j["source"].lower() != "linkedin_post" for j in results)
    assert len(results) == len(sample_jobs)


def test_exclude_source_accepts_comma_separated_list():
    """Added 2026-08-09 for the discovered-jobs "job sites" tab, which
    needs to exclude both linkedin_post and whatsapp_message sources at
    once — a single exclude_source value alone can't express that."""
    jobs = [
        {"title": "Real site job", "source": "tanqeeb"},
        {"title": "A LinkedIn post", "source": "linkedin_post"},
        {"title": "A WhatsApp message", "source": "whatsapp_message"},
    ]
    results = filter_jobs(jobs, exclude_source="linkedin_post,whatsapp_message")
    assert len(results) == 1
    assert results[0]["title"] == "Real site job"


def test_filter_by_review_status_exact_match():
    jobs = [
        {"title": "Applied job", "review_status": "applied"},
        {"title": "Not suitable job", "review_status": "not_suitable"},
        {"title": "Unreviewed job", "review_status": None},
    ]
    results = filter_jobs(jobs, review_status="applied")
    assert len(results) == 1
    assert results[0]["title"] == "Applied job"


def test_filter_by_review_status_none_returns_unreviewed_only():
    jobs = [
        {"title": "Applied job", "review_status": "applied"},
        {"title": "Unreviewed job", "review_status": None},
    ]
    results = filter_jobs(jobs, review_status="none")
    assert len(results) == 1
    assert results[0]["title"] == "Unreviewed job"


def test_router_integration_with_mock_jobs():
    from smarthunt.search.filtering import filter_jobs

    mock_service_jobs = [
        {
            "id": 1,
            "title": "OpenShift Platform Specialist",
            "location": "Riyadh",
            "source": "drjobs",
            "description": None,
        },
        {
            "id": 2,
            "title": "Senior Systems Engineer (IBM AIX)",
            "location": "Khobar",
            "source": "tanqeeb",
            "description": None,
        },
        {
            "id": 6,
            "title": "Linux Administrator",
            "location": "Jeddah",
            "source": "wzayef",
            "description": None,
        },
    ]

    # Test keyword search
    res_kw = filter_jobs(mock_service_jobs, keyword="linux")
    assert len(res_kw) == 1
    assert res_kw[0]["title"] == "Linux Administrator"

    # Test location search
    res_loc = filter_jobs(mock_service_jobs, location="riyadh")
    assert len(res_loc) == 1
    assert res_loc[0]["title"] == "OpenShift Platform Specialist"

    # Test source search
    res_src = filter_jobs(mock_service_jobs, source="tanqeeb")
    assert len(res_src) == 1
    assert res_src[0]["title"] == "Senior Systems Engineer (IBM AIX)"
