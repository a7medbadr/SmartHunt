from fastapi import APIRouter, status

from smarthunt.career.schemas import CareerAdviceRequest, CareerAdviceResponse
from smarthunt.career.service import CareerAdvisor

router = APIRouter()


@router.post("/advice", response_model=CareerAdviceResponse, status_code=status.HTTP_200_OK)
async def get_career_advice(payload: CareerAdviceRequest) -> CareerAdviceResponse:
    return CareerAdvisor.generate_advice(payload.resume)
