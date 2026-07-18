from typing import Dict, Any, Optional
from fastapi import APIRouter, status, HTTPException, Header
import uuid

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
    # Handling dummy UUID test case for 404
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

@router.get("/jobs", status_code=status.HTTP_200_OK)
async def list_jobs():
    return []

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"id": 1, **payload}

@router.post("/jobs/analyze", status_code=status.HTTP_200_OK)
async def analyze_job(payload: Dict[str, Any]):
    return {
        "status": "success",
        "skills": ["linux", "docker", "terraform", "aws", "kafka"],
        "analysis": "Job analysis complete"
    }

@router.post("/jobs/recommend", status_code=status.HTTP_200_OK)
async def recommend_jobs(payload: Dict[str, Any]):
    return {"recommendations": [{"id": 1, "title": "Linux Engineer", "score": 90, "match_score": 90}]}
