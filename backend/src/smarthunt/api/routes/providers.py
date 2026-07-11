from fastapi import APIRouter

from smarthunt.api.schemas import ProviderStatus
from smarthunt.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderStatus])
async def providers():

    return ProviderService().status()
