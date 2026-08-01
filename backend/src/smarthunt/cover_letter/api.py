from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.activity.models import ActivityType
from smarthunt.activity.service import log_activity
from smarthunt.api.dependencies import get_db
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
async def generate_cover_letter(
    payload: CoverLetterGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await cover_letter_service.generate_cover_letter(payload)

    await log_activity(
        db,
        ActivityType.COVER_LETTER_GENERATED,
        "تم إنشاء خطاب تقديم جديد",
    )

    return result
