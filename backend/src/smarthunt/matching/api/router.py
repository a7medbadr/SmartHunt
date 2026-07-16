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

@router.get("/details")
async def details():

    return {

        "overall":91,

        "skills":95,

        "experience":92,

        "education":88,

        "keywords":90

    }
