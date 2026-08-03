from email.message import EmailMessage

import aiosmtplib
import structlog

from smarthunt.core.config import settings

logger = structlog.get_logger("smarthunt")


async def send_email_message(subject: str, body: str) -> bool:
    """Best-effort real delivery via SMTP. Never raises — a failed
    external notification shouldn't break whatever real operation (e.g.
    an application being submitted) triggered it. Returns whether it
    actually sent. Mirrors channels/telegram.py's shape."""

    if not (
        settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
        and settings.smtp_from_email
        and settings.notification_email
    ):
        return False

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = settings.notification_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=True,
            timeout=15,
        )
        return True
    except Exception:
        logger.exception("email_notification_failed")
        return False
