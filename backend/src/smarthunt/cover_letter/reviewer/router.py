from fastapi import APIRouter, Depends, status

from smarthunt.cover_letter.reviewer.schemas import (
    CoverLetterReviewRequest,
    CoverLetterReviewResponse,
)
from smarthunt.cover_letter.reviewer.service import CoverLetterReviewer

router = APIRouter(prefix="/api/v1/cover-letter", tags=["cover-letter-reviewer"])


def get_cover_letter_reviewer() -> CoverLetterReviewer:
    return CoverLetterReviewer()


@router.post(
    "/review",
    response_model=CoverLetterReviewResponse,
    status_code=status.HTTP_200_OK,
)
def review_cover_letter(
    payload: CoverLetterReviewRequest,
    reviewer: CoverLetterReviewer = Depends(get_cover_letter_reviewer),
) -> CoverLetterReviewResponse:
    return reviewer.review_cover_letter(payload.cover_letter)
