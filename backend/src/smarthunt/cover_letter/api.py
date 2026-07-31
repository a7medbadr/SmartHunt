from fastapi import APIRouter, status

from smarthunt.cover_letter.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
)
from smarthunt.cover_letter.service import CoverLetterService

router = APIRouter()

cover_letter_service = CoverLetterService()


@router.post(
    "/generate",
    response_model=CoverLetterGenerateResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_cover_letter(payload: CoverLetterGenerateRequest):
    return await cover_letter_service.generate_cover_letter(payload)
