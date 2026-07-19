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


def test_router_integration_with_mock_jobs():
    from smarthunt.search.filtering import filter_jobs

    mock_service_jobs = [
        {"id": 1, "title": "OpenShift Platform Specialist", "location": "Riyadh", "source": "drjobs", "description": None},
        {"id": 2, "title": "Senior Systems Engineer (IBM AIX)", "location": "Khobar", "source": "tanqeeb", "description": None},
        {"id": 6, "title": "Linux Administrator", "location": "Jeddah", "source": "wzayef", "description": None},
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
