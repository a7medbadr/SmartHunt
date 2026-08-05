import pytest
from httpx import AsyncClient

from smarthunt.cover_letter.service import _truncate_for_ai


@pytest.mark.asyncio
async def test_cover_letter_generation(client: AsyncClient) -> None:
    payload = {
        "resume": "Linux Docker Python OpenShift",
        "job": "Linux Docker AWS Terraform",
    }
    response = await client.post("/api/v1/cover-letter/generate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "score" in data
    assert "matched_skills" in data
    assert "generated_cover_letter" in data

    assert isinstance(data["score"], int)
    assert isinstance(data["matched_skills"], list)
    assert len(data["generated_cover_letter"]) > 0


@pytest.mark.asyncio
async def test_cover_letter_is_not_the_old_static_template(client: AsyncClient) -> None:
    """Regression test: generate_cover_letter() used to be a hardcoded
    boilerplate string ("Dear Hiring Manager,\\n\\nI am excited to apply
    for the position...") with matched skill names slotted in — not AI
    generated at all, which is why every letter scored low on the
    reviewer's "too short"/"too generic" checks regardless of the real
    resume content. It now calls the real AI service (with a fallback
    template only if that call fails) and should read like it says
    something specific, not the fixed boilerplate sentence."""
    payload = {
        "resume": (
            "Senior Linux System Administrator with 8 years managing RHEL and AIX "
            "environments, led migration of 200+ servers to Red Hat OpenShift, "
            "reduced incident response time by 40% through Ansible automation."
        ),
        "job": "Senior System Administrator for Linux, RHEL, OpenShift required.",
    }
    response = await client.post("/api/v1/cover-letter/generate", json=payload)

    assert response.status_code == 200
    letter = response.json()["generated_cover_letter"]

    assert len(letter.split()) >= 40
    assert "i am excited to apply for the position." not in letter.lower()


@pytest.mark.asyncio
async def test_cover_letter_reflects_actual_overlap(client: AsyncClient) -> None:
    """The matched skills must come from the real resume/job overlap, not a
    fixed hardcoded list — resume and job here share nothing in the skills
    vocabulary, so matched_skills must be empty."""
    payload = {
        "resume": "Expert in graphic design and Adobe Photoshop",
        "job": "Looking for a barista with coffee experience",
    }
    response = await client.post("/api/v1/cover-letter/generate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["matched_skills"] == []
    assert "linux" not in data["generated_cover_letter"].lower()
    assert "docker" not in data["generated_cover_letter"].lower()


def test_truncate_for_ai_shortens_long_text():
    """Regression test: a full untruncated resume+job prompt was
    confirmed live 2026-08-03 to take 242s for a single AI call — far
    beyond what the frontend/proxy will wait for, the likely cause of
    reports that generation "hangs then returns nothing" with no error
    shown at all. Only the AI prompt is capped; match() still scores
    against the full text."""
    text = "a" * 5000
    truncated = _truncate_for_ai(text)
    assert len(truncated) < len(text)
    assert truncated.startswith("a" * 1500)
