from fastapi import APIRouter, Depends

from smarthunt.cover_letter.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
)
from smarthunt.cover_letter.service import CoverLetterService

router = APIRouter(prefix="/api/v1/cover-letter", tags=["cover-letter"])


def get_cover_letter_service() -> CoverLetterService:
    return CoverLetterService()


@router.post("/generate", response_model=CoverLetterGenerateResponse)
async def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    service: CoverLetterService = Depends(get_cover_letter_service),
) -> CoverLetterGenerateResponse:
    return await service.generate_cover_letter(request)
