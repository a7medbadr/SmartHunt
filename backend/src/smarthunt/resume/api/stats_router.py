from fastapi import APIRouter

router=APIRouter()

@router.get("/stats")
async def stats():

    return {
        "total_resumes":1,
        "average_score":91,
        "top_skill":"Linux"
    }
