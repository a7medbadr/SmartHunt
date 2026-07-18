from typing import Dict, Any
from fastapi import APIRouter, status

router = APIRouter()

@router.post("/advice", status_code=status.HTTP_200_OK)
async def get_career_advice(payload: Dict[str, Any]):
    return {
        "current_level": "Mid-Level",
        "recommended_roles": ["DevOps Engineer", "Linux Systems Administrator"],
        "advice": "Focus on Linux and Cloud Architecture",
        "next_steps": ["Learn Kubernetes", "Get RHCE"]
    }
