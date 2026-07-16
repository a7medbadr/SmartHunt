from fastapi import APIRouter
from smarthunt.search import search_service

router = APIRouter()

@router.get("/health")
async def provider_health():
    # بنرجع الـ status من الـ monitor المشترك اللي جوه السيرفيس الحية
    return search_service.monitor.all()
