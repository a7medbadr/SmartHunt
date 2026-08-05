import httpx
import structlog

from smarthunt.core.config import settings

logger = structlog.get_logger("smarthunt")


async def send_whatsapp_message(text: str) -> bool:
    """Best-effort real delivery via the 360dialog WhatsApp Sandbox API.
    Never raises — a failed external notification shouldn't break
    whatever real operation (e.g. an application being submitted)
    triggered it. Returns whether it actually sent. Mirrors
    channels/telegram.py's shape.

    Set WHATSAPP_API_KEY and WHATSAPP_RECIPIENT_NUMBER in secret.env
    (WHATSAPP_API_URL already defaults to the 360dialog sandbox
    endpoint via Settings, override only if using a different tier)."""

    if not (
        settings.whatsapp_api_key
        and settings.whatsapp_api_url
        and settings.whatsapp_recipient_number
    ):
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.whatsapp_api_url,
                headers={
                    "Content-Type": "application/json",
                    "D360-API-KEY": settings.whatsapp_api_key,
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": settings.whatsapp_recipient_number,
                    "type": "text",
                    "text": {"body": text},
                },
            )
            response.raise_for_status()
        return True
    except Exception:
        logger.exception("whatsapp_notification_failed")
        return False
