from fastapi import APIRouter, HTTPException

from smarthunt.ai.exceptions import AIError
from smarthunt.ai.service import ai_service
from smarthunt.ai.types import AIRequest, AIResponse


router = APIRouter(
    prefix="/ai",
)


@router.post(
    "/generate",
    response_model=AIResponse,
    tags=["ai"],
)
async def generate_ai_response(
    request: AIRequest,
) -> AIResponse:
    try:
        return await ai_service.generate(
            request,
        )

    except AIError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
