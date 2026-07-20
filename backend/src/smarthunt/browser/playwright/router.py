from fastapi import APIRouter

from smarthunt.browser.playwright.engine import playwright_engine
from smarthunt.browser.playwright.schemas import (
    ApplyRequest,
    DetectFormRequest,
    DetectFormResponse,
    LoginRequest,
    OpenJobRequest,
    OpenJobResponse,
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


@router.post("/open-job", response_model=OpenJobResponse)
async def open_job(payload: OpenJobRequest):
    return await playwright_engine.open_job(payload.job_url)


@router.post("/detect-form", response_model=DetectFormResponse)
async def detect_form(payload: DetectFormRequest):
    return await playwright_engine.detect_form(payload.job_url)


@router.post("/apply", response_model=StatusResponse)
async def apply(payload: ApplyRequest):
    return await playwright_engine.apply(payload.job_url)


@router.post("/screenshot", response_model=ScreenshotResponse)
async def screenshot():
    return await playwright_engine.take_screenshot()
