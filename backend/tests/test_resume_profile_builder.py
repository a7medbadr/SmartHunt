import pytest
import pytest_asyncio

from smarthunt.resume.profile_builder import ResumeProfileBuilder


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session):
    yield


@pytest.mark.asyncio
async def test_extract_email(client):
    profile = ResumeProfileBuilder().build("Email: badr@example.com")

    assert profile.email == "badr@example.com"


@pytest.mark.asyncio
async def test_extract_phone(client):
    profile = ResumeProfileBuilder().build("Phone: +966501234567")

    assert "+966501234567" in profile.phone


@pytest.mark.asyncio
async def test_extract_linkedin(client):
    profile = ResumeProfileBuilder().build("https://linkedin.com/in/badr")

    assert profile.linkedin == "https://linkedin.com/in/badr"


@pytest.mark.asyncio
async def test_extract_github(client):
    profile = ResumeProfileBuilder().build("https://github.com/badr")

    assert profile.github == "https://github.com/badr"


@pytest.mark.asyncio
async def test_extract_years(client):
    profile = ResumeProfileBuilder().build("I have 8 years of experience.")

    assert profile.years_of_experience == 8.0


@pytest.mark.asyncio
async def test_extract_skills(client):
    profile = ResumeProfileBuilder().build("Python Linux Docker OpenShift Git")

    assert "python" in profile.skills
    assert "linux" in profile.skills
    assert "docker" in profile.skills
    assert "openshift" in profile.skills
    assert "git" in profile.skills


@pytest.mark.asyncio
async def test_empty_resume(client):
    profile = ResumeProfileBuilder().build("")

    assert profile.email is None
    assert profile.phone is None
    assert profile.skills == []


@pytest.mark.asyncio
async def test_malformed_resume(client):
    profile = ResumeProfileBuilder().build("%%%% #### ????")

    assert profile.email is None
    assert profile.phone is None
    assert profile.linkedin is None
    assert profile.github is None
    assert profile.skills == []
