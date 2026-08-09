from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.whatsapp_monitor import service
from smarthunt.whatsapp_monitor.chat_scanner import (
    QR_CODE_SELECTOR,
    WHATSAPP_PROVIDER,
    WHATSAPP_WEB_URL,
    WhatsAppScanError,
    dismiss_login_overlays,
    is_logged_in,
    scan_chat,
)
from smarthunt.whatsapp_monitor.schemas import (
    MonitoredChatCreate,
    MonitoredChatResponse,
    MonitoredChatUpdate,
    ScanResultResponse,
    WhatsAppLoginStatusResponse,
)

router = APIRouter(prefix="/whatsapp-monitor", tags=["whatsapp-monitor"])

# QR-code screenshot: same "just a local file path, no StaticFiles mount"
# pattern PlaywrightEngine.take_screenshot already uses for /tmp/screenshots
# — this app runs as a single co-located container, so the filesystem is
# shared between whatever writes the screenshot and whatever serves it.
QR_SCREENSHOT_PATH = Path("/tmp/smarthunt/whatsapp/qr.png")


async def _screenshot_login_page(page) -> None:
    """Crops tightly to just the QR code when it's on screen instead of
    screenshotting the whole 1366x768 page — the QR only occupies a small
    corner of a full-page shot, which read as an unusably tiny, blurry
    square once actually viewed on a phone trying to scan it (found live
    2026-08-08 from direct owner feedback). Confirmed live the same day:
    the QR element isn't in the DOM immediately after navigation — it
    renders ~1-4s later — so this waits briefly for it rather than
    grabbing whatever's there right away (which was silently falling
    through to the full-page fallback below every time, the actual root
    cause of the too-small-to-scan screenshot). Falls back to a full-page
    screenshot when the QR never appears (already logged in, or genuinely
    not loaded yet) so login/status still shows something useful."""
    QR_SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        qr_element = page.locator(QR_CODE_SELECTOR).first
        await qr_element.wait_for(state="visible", timeout=8000)
        await qr_element.screenshot(path=str(QR_SCREENSHOT_PATH))
        return
    except Exception:
        pass
    await page.screenshot(path=str(QR_SCREENSHOT_PATH))


@router.get("/chats", response_model=list[MonitoredChatResponse])
async def list_chats(db: AsyncSession = Depends(get_db)):
    return await service.list_chats(db)


@router.post("/chats", response_model=MonitoredChatResponse, status_code=status.HTTP_201_CREATED)
async def add_chat(payload: MonitoredChatCreate, db: AsyncSession = Depends(get_db)):
    return await service.add_chat(db, payload.chat_url, payload.label, payload.chat_type)


@router.patch("/chats/{chat_id}", response_model=MonitoredChatResponse)
async def update_chat(
    chat_id: int, payload: MonitoredChatUpdate, db: AsyncSession = Depends(get_db)
):
    chat = await service.set_chat_enabled(db, chat_id, payload.enabled)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return chat


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await service.remove_chat(db, chat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")


@router.post("/chats/{chat_id}/scan", response_model=ScanResultResponse)
async def scan_chat_now(chat_id: int, db: AsyncSession = Depends(get_db)):
    chats = await service.list_chats(db)
    chat = next((c for c in chats if c.id == chat_id), None)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    try:
        messages = await scan_chat(chat.label, chat.chat_url, chat.chat_type)
    except WhatsAppScanError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.reason) from exc

    saved = await service.scan_and_save(db, messages)
    await service.mark_chat_checked(db, chat_id)

    return ScanResultResponse(
        scanned=len(messages), saved=len(saved), job_ids=[job.id for job in saved]
    )


@router.post("/login/start", response_model=WhatsAppLoginStatusResponse)
async def start_login():
    """Opens WhatsApp Web on a dedicated, persistent browser profile
    (get_persistent_page — see its docstring for why this needs a real
    on-disk profile rather than the cookie-snapshot approach every other
    provider uses) and screenshots whatever it currently shows (a QR code
    if logged out, the chat list if a previously-linked session is still
    valid) — first step of the one-time QR-login bootstrap. A previously
    successful login survives indefinitely on disk, so this can also just
    confirm "still logged in" after a restart with no QR needed at all."""
    try:
        page = await browser_manager.get_persistent_page(WHATSAPP_PROVIDER)

        if "web.whatsapp.com" not in page.url:
            await page.goto(WHATSAPP_WEB_URL, wait_until="domcontentloaded", timeout=30000)

        logged_in = await is_logged_in(page)
        if logged_in:
            await dismiss_login_overlays(page)

        # Best-effort — a slow/failed screenshot (host CPU contention,
        # see CLAUDE.md's Chromium-contention notes) shouldn't fail the
        # whole login check when `logged_in` above already has a real
        # answer; found live 2026-08-09 when a screenshot timeout turned
        # an actually-successful login into a reported failure.
        try:
            await _screenshot_login_page(page)
        except Exception:
            pass

        return WhatsAppLoginStatusResponse(logged_in=logged_in)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"مش قادرين نفتح واتساب ويب دلوقتي: {exc}",
        ) from exc


@router.get("/login/status", response_model=WhatsAppLoginStatusResponse)
async def login_status():
    """Re-checks the same page (no re-navigation) for the logged-in
    marker — meant to be polled every few seconds by the frontend while
    the owner scans the QR with their phone. Refreshes the screenshot
    either way, since WhatsApp Web's QR code itself rotates every
    ~20-60s. Doesn't launch a browser just to answer this — has_
    persistent_page returns False with no side effects until /login/start
    has actually been called once."""
    if not browser_manager.has_persistent_page(WHATSAPP_PROVIDER):
        return WhatsAppLoginStatusResponse(logged_in=False)

    try:
        page = await browser_manager.get_persistent_page(WHATSAPP_PROVIDER)
        logged_in = await is_logged_in(page)

        if logged_in:
            await dismiss_login_overlays(page)

        # Best-effort — a slow/failed screenshot (host CPU contention,
        # see CLAUDE.md's Chromium-contention notes) shouldn't fail the
        # whole login check when `logged_in` above already has a real
        # answer; found live 2026-08-09 when a screenshot timeout turned
        # an actually-successful login into a reported failure.
        try:
            await _screenshot_login_page(page)
        except Exception:
            pass

        return WhatsAppLoginStatusResponse(logged_in=logged_in)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"مش قادرين نتأكد من حالة تسجيل الدخول دلوقتي: {exc}",
        ) from exc


@router.get("/login/qr-image")
async def get_qr_image():
    if not QR_SCREENSHOT_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لسه مفيش صورة QR — دوس على زرار ربط واتساب الأول.",
        )
    return FileResponse(str(QR_SCREENSHOT_PATH), media_type="image/png")
