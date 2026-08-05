import email.utils
import imaplib
import email as email_lib
from email.message import EmailMessage as MimeMessage
from email.header import decode_header

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.ai.service import ai_service
from smarthunt.ai.types import AIRequest
from smarthunt.core.config import settings
from smarthunt.database.models.application import Application
from smarthunt.email_apply.models import EmailMessage
from smarthunt.logging.logger import logger
from smarthunt.notifications.schemas import NotificationCreate
from smarthunt.notifications.service import NotificationService

notification_service = NotificationService()

# Same reasoning as cover_letter/service.py and resume/services/tailoring.py
# — only the prompt fed to the AI is capped, never anything actually sent.
# Halved from 3000 2026-08-04 (see cover_letter/service.py's comment for
# the live-measured numbers behind this) — cuts prompt-eval time roughly
# in half, which is what actually lets an attempt finish inside its
# timeout budget instead of being cancelled and retried.
_MAX_CHARS_FOR_AI = 1500


def _truncate_for_ai(text: str) -> str:
    if len(text) <= _MAX_CHARS_FOR_AI:
        return text
    return text[:_MAX_CHARS_FOR_AI] + "\n...(truncated)"


DRAFT_PROMPT = """You are a job applicant emailing a hiring contact directly to apply for a role \
(this posting asks candidates to send their CV by email rather than through a form). Write a \
short, professional application email (100-150 words) in the same language as the job description \
below. Use only real details from the resume — do not invent experience. Reference the job title \
and company if given. Mention one concrete, relevant piece of experience, not just a skills list. \
End by saying the CV is attached/included. Output ONLY the email body text — no subject line, no \
headers, no explanation, no placeholders.

Resume:
{resume}

Job title: {job_title}
Company: {company}
Job description:
{job}
"""

FALLBACK_SUBJECT = "Application for {job_title}"
FALLBACK_BODY = (
    "Dear Hiring Manager,\n\n"
    "I would like to apply for the {job_title} position at {company}. "
    "My background includes {skills}, and I believe my experience aligns well with this role. "
    "Please find my CV attached — I would welcome the opportunity to discuss further.\n\n"
    "Best regards"
)

REPLY_DRAFT_PROMPT = """You are a job applicant replying to a hiring contact's email during an \
active job application conversation. Write a short, professional reply (60-120 words) in the same \
language as their message below. Address what they actually asked or said — do not invent new \
claims about the candidate's experience beyond the resume. Output ONLY the reply body text, no \
subject line, no headers, no explanation.

Resume:
{resume}

Their message:
{incoming_message}
"""


async def draft_application_email(
    resume_text: str,
    job_title: str,
    company: str,
    job_description: str,
    matched_skills: list[str],
) -> dict:
    # The subject is always computed programmatically, never left to the
    # AI — confirmed live 2026-08-03 that the small local model, when
    # asked to fill in a "SUBJECT: <one line subject>" template slot,
    # sometimes echoes the placeholder text itself back verbatim instead
    # of replacing it. A plain "Application for {job_title}" is more
    # reliable than anything worth the risk of a literal "<one line
    # subject>" landing in a real sent email.
    subject = FALLBACK_SUBJECT.format(job_title=job_title)
    fallback_body = FALLBACK_BODY.format(
        job_title=job_title,
        company=company,
        skills=", ".join(matched_skills) if matched_skills else "relevant technical skills",
    )

    try:
        ai_response = await ai_service.generate(
            AIRequest(
                prompt=DRAFT_PROMPT.format(
                    resume=_truncate_for_ai(resume_text),
                    job_title=job_title,
                    company=company,
                    job=_truncate_for_ai(job_description),
                ),
                max_tokens=350,
                timeout=220.0,
            )
        )
        if ai_response.provider.value == "local":
            return {"subject": subject, "body": fallback_body}

        body = ai_response.content.strip()
        return {"subject": subject, "body": body or fallback_body}
    except Exception:
        logger.exception("email_apply_draft_failed")
        return {"subject": subject, "body": fallback_body}


async def draft_reply(resume_text: str, incoming_message: str) -> str:
    try:
        ai_response = await ai_service.generate(
            AIRequest(
                prompt=REPLY_DRAFT_PROMPT.format(
                    resume=_truncate_for_ai(resume_text),
                    incoming_message=_truncate_for_ai(incoming_message),
                ),
                max_tokens=250,
                timeout=220.0,
            )
        )
        if ai_response.provider.value == "local":
            return ""
        return ai_response.content.strip()
    except Exception:
        logger.exception("email_apply_reply_draft_failed")
        return ""


async def send_application_email(
    db: AsyncSession,
    application_id,
    recipient_email: str,
    subject: str,
    body: str,
) -> EmailMessage:
    return await _send_email(db, application_id, recipient_email, subject, body, in_reply_to=None)


async def send_reply(
    db: AsyncSession,
    application_id,
    recipient_email: str,
    subject: str,
    body: str,
    in_reply_to: str,
) -> EmailMessage:
    return await _send_email(
        db, application_id, recipient_email, subject, body, in_reply_to=in_reply_to
    )


async def _send_email(
    db: AsyncSession,
    application_id,
    recipient_email: str,
    subject: str,
    body: str,
    in_reply_to: str | None,
) -> EmailMessage:
    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password):
        raise RuntimeError("SMTP is not configured — cannot send application emails.")

    message_id = email.utils.make_msgid()

    mime_message = MimeMessage()
    mime_message["Message-ID"] = message_id
    mime_message["From"] = settings.smtp_from_email or settings.smtp_username
    mime_message["To"] = recipient_email
    mime_message["Subject"] = subject
    if in_reply_to:
        mime_message["In-Reply-To"] = in_reply_to
        mime_message["References"] = in_reply_to
    mime_message.set_content(body)

    await aiosmtplib.send(
        mime_message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=True,
        timeout=20,
    )

    record = EmailMessage(
        application_id=application_id,
        direction="outbound",
        from_address=settings.smtp_from_email or settings.smtp_username,
        to_address=recipient_email,
        subject=subject,
        body=body,
        message_id=message_id,
        in_reply_to=in_reply_to,
        read_by_owner=True,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return record


def _decode_mime_header(raw: str | None) -> str:
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = ""
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get(
                "Content-Disposition", ""
            ).startswith("attachment"):
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _poll_imap_sync(tracked_message_ids: list[str]) -> list[dict]:
    """Runs synchronously (imaplib has no async API) — always called via
    asyncio.to_thread from check_for_replies(). Searches the inbox for
    any message whose References/In-Reply-To header references one of
    our own sent Message-IDs, i.e. a real reply to an application email
    we sent — the same threading mechanism any real mail client uses."""
    found: list[dict] = []

    if not (settings.imap_host and settings.smtp_username and settings.smtp_password):
        return found

    conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    try:
        conn.login(settings.smtp_username, settings.smtp_password)
        conn.select("INBOX")

        for message_id in tracked_message_ids:
            status, data = conn.search(None, f'HEADER REFERENCES "{message_id}"')
            if status != "OK":
                continue

            ids = data[0].split()
            for uid in ids:
                status, msg_data = conn.fetch(uid, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)

                found.append(
                    {
                        "from_address": email.utils.parseaddr(msg.get("From", ""))[1],
                        "subject": _decode_mime_header(msg.get("Subject")),
                        "body": _extract_body(msg),
                        "message_id": msg.get("Message-ID", "").strip(),
                        "in_reply_to": message_id,
                    }
                )
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    return found


async def check_for_replies(db: AsyncSession) -> list[EmailMessage]:
    import asyncio

    outbound_result = await db.execute(
        select(EmailMessage.message_id, EmailMessage.application_id).where(
            EmailMessage.direction == "outbound"
        )
    )
    outbound = {row.message_id: row.application_id for row in outbound_result}

    if not outbound:
        return []

    existing_result = await db.execute(
        select(EmailMessage.message_id).where(EmailMessage.direction == "inbound")
    )
    already_seen = {row.message_id for row in existing_result}

    try:
        raw_replies = await asyncio.to_thread(_poll_imap_sync, list(outbound.keys()))
    except Exception:
        logger.exception("email_apply_imap_poll_failed")
        return []

    created: list[EmailMessage] = []

    for reply in raw_replies:
        if not reply["message_id"] or reply["message_id"] in already_seen:
            continue

        application_id = outbound.get(reply["in_reply_to"])
        if application_id is None:
            continue

        record = EmailMessage(
            application_id=application_id,
            direction="inbound",
            from_address=reply["from_address"],
            to_address=settings.smtp_username or "",
            subject=reply["subject"],
            body=reply["body"],
            message_id=reply["message_id"],
            in_reply_to=reply["in_reply_to"],
            read_by_owner=False,
        )
        db.add(record)
        created.append(record)
        already_seen.add(reply["message_id"])

        app_result = await db.execute(select(Application).where(Application.id == application_id))
        application = app_result.scalar_one_or_none()
        job_title = application.job_title if application else "الوظيفة"

        try:
            await notification_service.create(
                db,
                NotificationCreate(
                    type="EMAIL_REPLY",
                    title=f"وصل رد على تقديم: {job_title}",
                    message=(
                        f"من: {reply['from_address']}\n"
                        f"الموضوع: {reply['subject']}\n\n"
                        f"{reply['body'][:500]}"
                    ),
                    channel="TELEGRAM",
                    priority="HIGH",
                ),
            )
            await notification_service.create(
                db,
                NotificationCreate(
                    type="EMAIL_REPLY",
                    title=f"وصل رد على تقديم: {job_title}",
                    message=(
                        f"من: {reply['from_address']}\n"
                        f"الموضوع: {reply['subject']}\n\n"
                        f"{reply['body'][:500]}"
                    ),
                    channel="WHATSAPP",
                    priority="HIGH",
                ),
            )
        except Exception:
            logger.exception("email_apply_reply_notification_failed")

    if created:
        await db.flush()
        for record in created:
            await db.refresh(record)

    return created
