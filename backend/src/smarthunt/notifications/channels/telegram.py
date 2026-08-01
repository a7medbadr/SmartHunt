import httpx
import structlog

from smarthunt.core.config import settings

logger = structlog.get_logger("smarthunt")

TELEGRAM_API_BASE = "https://api.telegram.org"


async def send_telegram_message(text: str) -> bool:
    """Best-effort real delivery via the Telegram Bot API. Never raises —
    a failed external notification shouldn't break whatever real
    operation (e.g. an application being submitted) triggered it. Returns
    whether it actually sent."""

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False

    url = f"{TELEGRAM_API_BASE}/bot{settings.telegram_bot_token}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": settings.telegram_chat_id,
                    "text": text,
                },
            )
            response.raise_for_status()
        return True
    except Exception:
        logger.exception("telegram_notification_failed")
        return False
