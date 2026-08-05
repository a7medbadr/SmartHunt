import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.activity.models import ActivityType
from smarthunt.activity.service import log_activity
from smarthunt.api.dependencies import get_db
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.email_apply.extraction import extract_email
from smarthunt.email_apply.models import EmailMessage
from smarthunt.email_apply.schemas import (
    DraftEmailRequest,
    DraftEmailResponse,
    DraftReplyResponse,
    EmailMessageResponse,
    SendEmailRequest,
    SendReplyRequest,
)
from smarthunt.email_apply.service import (
    draft_application_email,
    draft_reply,
    send_application_email,
    send_reply,
)
from smarthunt.matching.services.matcher import match

router = APIRouter(prefix="/email-apply", tags=["email-apply"])


async def _get_resume_text(db: AsyncSession) -> str | None:
    result = await db.execute(select(Resume).order_by(Resume.updated_at.desc()).limit(1))
    resume = result.scalar_one_or_none()
    return resume.extracted_text if resume else None


def _job_description_text(job: Job) -> str:
    return "\n".join(part for part in (job.description, job.requirements) if part)


@router.post("/draft", response_model=DraftEmailResponse)
async def draft_email(payload: DraftEmailRequest, db: AsyncSession = Depends(get_db)):
    job_result = await db.execute(select(Job).where(Job.id == payload.job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    recipient_email = extract_email(job.description, job.requirements)
    if recipient_email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No contact email found in this job's description.",
        )

    resume_text = await _get_resume_text(db)
    if not resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No resume uploaded yet."
        )

    job_text = _job_description_text(job)
    match_result = match(resume_text=resume_text, job_text=job_text)

    draft = await draft_application_email(
        resume_text=resume_text,
        job_title=job.title,
        company=job.company,
        job_description=job_text,
        matched_skills=match_result["matched_skills"],
    )

    return DraftEmailResponse(
        recipient_email=recipient_email,
        subject=draft["subject"],
        body=draft["body"],
    )


@router.post("/send", response_model=EmailMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_email(payload: SendEmailRequest, db: AsyncSession = Depends(get_db)):
    job_result = await db.execute(select(Job).where(Job.id == payload.job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    application = Application(
        job_title=job.title,
        company=job.company,
        url=job.url,
        status="Applied",
        job_id=job.id,
    )
    db.add(application)
    await db.flush()
    await db.refresh(application)

    try:
        message = await send_application_email(
            db,
            application.id,
            payload.recipient_email,
            payload.subject,
            payload.body,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to send email: {exc}"
        )

    await log_activity(
        db,
        ActivityType.APPLICATION_CREATED,
        f"تم التقديم بالإيميل على: {job.title} في {job.company}",
    )
    await db.commit()

    return message


@router.get("/{application_id}/thread", response_model=list[EmailMessageResponse])
async def get_thread(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.application_id == application_id)
        .order_by(EmailMessage.created_at.asc())
    )
    return list(result.scalars().all())


@router.post("/{application_id}/reply/draft", response_model=DraftReplyResponse)
async def draft_reply_endpoint(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    latest_inbound = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.application_id == application_id, EmailMessage.direction == "inbound")
        .order_by(EmailMessage.created_at.desc())
        .limit(1)
    )
    incoming = latest_inbound.scalar_one_or_none()
    if incoming is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reply to respond to yet."
        )

    resume_text = await _get_resume_text(db)
    body = await draft_reply(resume_text or "", incoming.body)

    return DraftReplyResponse(body=body)


@router.post(
    "/{application_id}/reply/send",
    response_model=EmailMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_reply_endpoint(
    application_id: uuid.UUID, payload: SendReplyRequest, db: AsyncSession = Depends(get_db)
):
    latest_inbound = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.application_id == application_id, EmailMessage.direction == "inbound")
        .order_by(EmailMessage.created_at.desc())
        .limit(1)
    )
    incoming = latest_inbound.scalar_one_or_none()
    if incoming is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reply to respond to yet."
        )

    reply_subject = incoming.subject
    if not reply_subject.lower().startswith("re:"):
        reply_subject = f"Re: {reply_subject}"

    try:
        message = await send_reply(
            db,
            application_id,
            incoming.from_address,
            reply_subject,
            payload.body,
            incoming.message_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to send reply: {exc}"
        )

    await db.commit()

    return message
