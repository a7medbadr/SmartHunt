from fastapi import APIRouter

from smarthunt.browser.playwright.engine import playwright_engine
from smarthunt.browser.playwright.schemas import (
    ApplyRequest,
    LoginRequest,
    ScreenshotResponse,
    StatusResponse,
)

router = APIRouter(prefix="", tags=["playwright"])


@router.post("/start", response_model=StatusResponse)
async def start_engine():
    return await playwright_engine.start()


@router.post("/stop", response_model=StatusResponse)
async def stop_engine():
    return await playwright_engine.stop()


@router.post("/login", response_model=StatusResponse)
async def login(payload: LoginRequest):
    return await playwright_engine.login(payload.provider)


@router.post("/apply", response_model=StatusResponse)
async def apply(payload: ApplyRequest):
    return await playwright_engine.apply(payload.job_url)


@router.post("/screenshot", response_model=ScreenshotResponse)
async def screenshot():
    return await playwright_engine.take_screenshot()
