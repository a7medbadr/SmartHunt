from fastapi import APIRouter, Depends, status

from smarthunt.resume.reviewer.schemas import (
    ResumeReviewRequest,
    ResumeReviewResponse,
)
from smarthunt.resume.reviewer.service import ResumeReviewer

router = APIRouter(tags=["resume-reviewer"])


def get_resume_reviewer() -> ResumeReviewer:
    return ResumeReviewer()


@router.post(
    "/review",
    response_model=ResumeReviewResponse,
    status_code=status.HTTP_200_OK,
)
def review_resume(
    payload: ResumeReviewRequest,
    reviewer: ResumeReviewer = Depends(get_resume_reviewer),
) -> ResumeReviewResponse:
    return reviewer.review_resume(payload.resume)
