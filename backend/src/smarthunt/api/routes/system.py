from fastapi import APIRouter

router=APIRouter()

@router.get("/summary")
async def summary():

    return {

        "status":"healthy",

        "database":"up",

        "api":"up",

        "metrics":"up"

    }
