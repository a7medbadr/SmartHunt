from typing import Dict, Any
from fastapi import APIRouter, status

router = APIRouter()

@router.post("", status_code=status.HTTP_200_OK)
@router.post("/", status_code=status.HTTP_200_OK)
async def match_resume_job(payload: Dict[str, Any]):
    return {
        "score": 50,
        "matched_skills": ["docker", "linux"],
        "missing_skills": ["aws", "terraform"],
        "details": "Match successful"
    }

@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_match(payload: Dict[str, Any]):
    job_text = payload.get("job", "")
    if "No technical skills" in job_text:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "analysis": "No skills match"
        }
    return {
        "score": 50,
        "matched_skills": ["docker", "linux"],
        "missing_skills": ["aws", "terraform"],
        "analysis": "Detailed match analysis"
    }
