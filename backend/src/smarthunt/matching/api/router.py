from fastapi import APIRouter

router = APIRouter()

@router.get("/score")
async def score():
    return {
        "score":91,
        "status":"excellent"
    }

@router.get("/recommendations")
async def recommendations():
    return {
        "recommendations":[
            "Senior Linux Engineer",
            "OpenShift Administrator",
            "Platform Engineer"
        ]
    }
