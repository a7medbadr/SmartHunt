from fastapi import APIRouter

from smarthunt.cover_letter.reviewer.schemas import (
    CoverLetterReviewRequest,
    CoverLetterReviewResponse,
)
from smarthunt.cover_letter.reviewer.service import CoverLetterReviewer

router = APIRouter()

_reviewer = CoverLetterReviewer()


@router.post("/review", response_model=CoverLetterReviewResponse)
def review_cover_letter(request: CoverLetterReviewRequest) -> CoverLetterReviewResponse:
    return _reviewer.review_cover_letter(request.cover_letter)
