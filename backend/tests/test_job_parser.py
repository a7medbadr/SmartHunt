from smarthunt.matching.job_parser import extract_job_skills


def test_extract_job_skills_success():
    text = "We are looking for a Senior Linux Engineer with experience in Docker, CI/CD, PostgreSQL, and RHEL."
    skills = extract_job_skills(text)
    assert "linux" in skills
    assert "docker" in skills
    assert "ci/cd" in skills
    assert "postgresql" in skills
    assert "rhel" in skills


def test_extract_job_skills_empty():
    assert extract_job_skills("") == []
    assert extract_job_skills("   ") == []


def test_extract_job_skills_no_duplicates():
    text = "Linux linux LINUX Docker docker PostgreSQL postgresql C++ C++"
    skills = extract_job_skills(text)
    assert len(skills) == len(set(skills))
    assert "linux" in skills
    assert "docker" in skills
    assert "c++" in skills
