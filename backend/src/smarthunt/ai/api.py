from fastapi import APIRouter

from smarthunt.ai.health import ai_health_check
from smarthunt.ai.service import ai_service
from smarthunt.ai.types import AIRequest, AIResponse


router = APIRouter(
    prefix="/ai",
)


@router.post(
    "/generate",
    response_model=AIResponse,
)
async def generate_ai(
    request: AIRequest,
) -> AIResponse:

    return await ai_service.generate(
        request
    )


@router.get(
    "/health",
)
async def health_ai():

    return await ai_health_check()
