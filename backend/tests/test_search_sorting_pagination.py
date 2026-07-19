import pytest
from smarthunt.search.filtering import filter_jobs, sort_jobs, paginate_jobs


@pytest.fixture
def sample_jobs():
    return [
        {
            "id": 1,
            "title": "Senior Linux System Administrator",
            "location": "Riyadh",
            "source": "LinkedIn",
            "description": "RedHat OpenShift",
        },
        {
            "id": 2,
            "title": "Python Developer",
            "location": "Abu Dhabi",
            "source": "Wuzzuf",
            "description": "FastAPI backend",
        },
        {
            "id": 3,
            "title": "DevOps Engineer",
            "location": "Cairo",
            "source": "Indeed",
            "description": "Linux and Docker",
        },
        {
            "id": 4,
            "title": "Cloud Architect",
            "location": "Doha",
            "source": "Bayt",
            "description": "AWS Azure GCP",
        },
        {
            "id": 5,
            "title": "AI Research Scientist",
            "location": "Riyadh",
            "source": "LinkedIn",
            "description": "Machine Learning",
        },
    ]


def test_sort_by_title_asc(sample_jobs):
    sorted_res = sort_jobs(sample_jobs, sort_by="title", order="asc")
    titles = [j["title"] for j in sorted_res]
    assert titles == [
        "AI Research Scientist",
        "Cloud Architect",
        "DevOps Engineer",
        "Python Developer",
        "Senior Linux System Administrator",
    ]


def test_sort_by_title_desc(sample_jobs):
    sorted_res = sort_jobs(sample_jobs, sort_by="title", order="desc")
    titles = [j["title"] for j in sorted_res]
    assert titles == [
        "Senior Linux System Administrator",
        "Python Developer",
        "DevOps Engineer",
        "Cloud Architect",
        "AI Research Scientist",
    ]


def test_sort_by_location_asc(sample_jobs):
    sorted_res = sort_jobs(sample_jobs, sort_by="location", order="asc")
    locations = [j["location"] for j in sorted_res]
    assert locations == ["Abu Dhabi", "Cairo", "Doha", "Riyadh", "Riyadh"]


def test_sort_by_source_asc(sample_jobs):
    sorted_res = sort_jobs(sample_jobs, sort_by="source", order="asc")
    sources = [j["source"] for j in sorted_res]
    assert sources == ["Bayt", "Indeed", "LinkedIn", "LinkedIn", "Wuzzuf"]


def test_pagination_first_page(sample_jobs):
    paged, total = paginate_jobs(sample_jobs, page=1, limit=2)
    assert total == 5
    assert len(paged) == 2
    assert paged[0]["id"] == 1
    assert paged[1]["id"] == 2


def test_pagination_second_page(sample_jobs):
    paged, total = paginate_jobs(sample_jobs, page=2, limit=2)
    assert total == 5
    assert len(paged) == 2
    assert paged[0]["id"] == 3
    assert paged[1]["id"] == 4


def test_pagination_last_page(sample_jobs):
    paged, total = paginate_jobs(sample_jobs, page=3, limit=2)
    assert total == 5
    assert len(paged) == 1
    assert paged[0]["id"] == 5


def test_combined_filter_sort_paginate(sample_jobs):
    # 1. Filter by location = Riyadh
    filtered = filter_jobs(sample_jobs, location="riyadh")
    assert len(filtered) == 2

    # 2. Sort by title asc
    sorted_res = sort_jobs(filtered, sort_by="title", order="asc")
    assert sorted_res[0]["title"] == "AI Research Scientist"
    assert sorted_res[1]["title"] == "Senior Linux System Administrator"

    # 3. Paginate page=1, limit=1
    paged, total = paginate_jobs(sorted_res, page=1, limit=1)
    assert total == 2
    assert len(paged) == 1
    assert paged[0]["title"] == "AI Research Scientist"
