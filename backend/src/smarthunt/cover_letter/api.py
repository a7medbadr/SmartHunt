from typing import Any, Dict

from fastapi import APIRouter, status

router = APIRouter()


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_cover_letter(payload: Dict[str, Any]):
    return {
        "cover_letter": "Generated cover letter text...",
        "generated_cover_letter": "Generated cover letter text...",
        "score": 85,
        "matched_skills": ["linux", "docker"],
    }
