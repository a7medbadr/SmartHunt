from typing import Any, Dict

from fastapi import APIRouter, status

from smarthunt.resume.parser.skills import extract_skills

router = APIRouter()


@router.post("/jobs/analyze", status_code=status.HTTP_200_OK)
async def analyze_job(payload: Dict[str, Any]):
    description = payload.get("description", "")
    skills = extract_skills(description)
    return {
        "status": "success",
        "skills": skills,
        "analysis": f"Found {len(skills)} matching skill(s) in the job description",
    }
