from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.job_notes.schemas import JobNoteCreate, JobNoteResponse, JobNoteUpdate
from smarthunt.job_notes.service import JobNoteNotFoundError, job_note_service

router = APIRouter(prefix="", tags=["job-notes"])


@router.post("", response_model=JobNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_job_note(payload: JobNoteCreate, db: AsyncSession = Depends(get_db)):
    return await job_note_service.create_note(db, payload)


@router.get("/{job_id}", response_model=List[JobNoteResponse])
async def list_job_notes(job_id: int, db: AsyncSession = Depends(get_db)):
    return await job_note_service.list_notes_by_job(db, job_id)


@router.patch("/{note_id}", response_model=JobNoteResponse)
async def update_job_note(
    note_id: int, payload: JobNoteUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        return await job_note_service.update_note(db, note_id, payload)
    except JobNoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_note(note_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await job_note_service.delete_note(db, note_id)
    except JobNoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
