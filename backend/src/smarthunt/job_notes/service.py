from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.job_notes.models import JobNote
from smarthunt.job_notes.schemas import JobNoteCreate, JobNoteUpdate


class JobNoteNotFoundError(Exception):
    pass


class JobNoteService:
    async def create_note(self, db: AsyncSession, data: JobNoteCreate) -> JobNote:
        note = JobNote(job_id=data.job_id, note=data.note)
        db.add(note)
        await db.flush()
        await db.refresh(note)
        return note

    async def list_notes_by_job(self, db: AsyncSession, job_id: int) -> List[JobNote]:
        result = await db.execute(
            select(JobNote).where(JobNote.job_id == job_id).order_by(JobNote.created_at)
        )
        return list(result.scalars().all())

    async def get_note(self, db: AsyncSession, note_id: int) -> JobNote:
        result = await db.execute(select(JobNote).where(JobNote.id == note_id))
        note = result.scalar_one_or_none()
        if note is None:
            raise JobNoteNotFoundError(f"Job note with id {note_id} not found")
        return note

    async def update_note(self, db: AsyncSession, note_id: int, data: JobNoteUpdate) -> JobNote:
        note = await self.get_note(db, note_id)
        note.note = data.note
        await db.flush()
        await db.refresh(note)
        return note

    async def delete_note(self, db: AsyncSession, note_id: int) -> None:
        note = await self.get_note(db, note_id)
        await db.delete(note)
        await db.flush()


job_note_service = JobNoteService()
