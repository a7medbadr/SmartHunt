import pytest
import pytest_asyncio

from smarthunt.domain.resume_profile import ResumeProfile


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session):
    yield


@pytest.mark.asyncio
async def test_create_profile(client):
    profile = ResumeProfile(
        full_name="Badr",
        email="badr@example.com",
    )

    assert profile.full_name == "Badr"
    assert profile.email == "badr@example.com"
    assert profile.skills == []
    assert profile.languages == []
    assert profile.certifications == []
    assert profile.projects == []


@pytest.mark.asyncio
async def test_to_dict(client):
    profile = ResumeProfile(
        full_name="Badr",
        email="badr@example.com",
        skills=["Python", "Linux"],
    )

    data = profile.to_dict()

    assert data["full_name"] == "Badr"
    assert data["email"] == "badr@example.com"
    assert data["skills"] == ["Python", "Linux"]


@pytest.mark.asyncio
async def test_from_dict(client):
    profile = ResumeProfile.from_dict(
        {
            "full_name": "Ahmed",
            "email": "ahmed@test.com",
            "skills": ["Docker"],
        }
    )

    assert profile.full_name == "Ahmed"
    assert profile.email == "ahmed@test.com"
    assert profile.skills == ["Docker"]


@pytest.mark.asyncio
async def test_merge(client):
    left = ResumeProfile(
        full_name="Badr",
        email="badr@example.com",
    )

    right = ResumeProfile(
        full_name="Another",
        phone="+966500000000",
    )

    left.merge(right)

    assert left.full_name == "Badr"
    assert left.email == "badr@example.com"
    assert left.phone == "+966500000000"


@pytest.mark.asyncio
async def test_merge_lists(client):
    left = ResumeProfile(
        skills=["Python"],
        languages=["Arabic"],
    )

    right = ResumeProfile(
        skills=["Python", "Docker"],
        languages=["English"],
    )

    left.merge(right)

    assert left.skills == ["Python", "Docker"]
    assert left.languages == ["Arabic", "English"]


@pytest.mark.asyncio
async def test_missing_values(client):
    profile = ResumeProfile()

    assert profile.email is None
    assert profile.phone is None
    assert profile.current_company is None
    assert profile.skills == []
    assert profile.languages == []
