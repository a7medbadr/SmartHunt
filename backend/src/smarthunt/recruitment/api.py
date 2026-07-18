import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from smarthunt.resume.parser.skills import extract_skills

router = APIRouter()

_applications_db = []

VALID_STATUSES = {"Applied", "Interviewing", "Offered", "Rejected", "Pending", "Technical Interview"}


@router.get("/applications", status_code=status.HTTP_200_OK)
async def list_applications():
    return _applications_db


@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def create_application(payload: Dict[str, Any]):
    app_status = payload.get("status")
    if app_status and app_status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid status")

    app_data = {"id": len(_applications_db) + 1, **payload}
    _applications_db.append(app_data)
    return app_data


@router.patch("/applications/{app_id}", status_code=status.HTTP_200_OK)
async def update_application(app_id: str, payload: Dict[str, Any]):
    try:
        uuid.UUID(app_id)
        raise HTTPException(status_code=404, detail="Application not found")
    except ValueError:
        pass

    int_id = int(app_id)
    for app in _applications_db:
        if app.get("id") == int_id:
            app.update(payload)
            return app

    raise HTTPException(status_code=404, detail="Application not found")


@router.delete("/applications/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(app_id: int):
    global _applications_db
    _applications_db = [app for app in _applications_db if app.get("id") != app_id]
    return None


@router.post("/jobs/analyze", status_code=status.HTTP_200_OK)
async def analyze_job(payload: Dict[str, Any]):
    description = payload.get("description", "")
    skills = extract_skills(description)
    return {
        "status": "success",
        "skills": skills,
        "analysis": f"Found {len(skills)} matching skill(s) in the job description",
    }
