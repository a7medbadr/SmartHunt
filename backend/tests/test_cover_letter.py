import pytest
from httpx import AsyncClient


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
