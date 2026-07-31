from fastapi import APIRouter, HTTPException

from smarthunt.scheduler.jobs import (
    discover_devops,
    discover_linux,
    discover_python,
)

router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
)


SCHEDULED_TASKS = {
    "python": discover_python,
    "linux": discover_linux,
    "devops": discover_devops,
}


@router.post("/trigger/{task_name}")
async def trigger_scheduler_task(
    task_name: str,
):

    task = SCHEDULED_TASKS.get(task_name)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scheduler task: {task_name}",
        )

    try:
        result = await task()

        return {
            "status": "SUCCESS",
            "task": task_name,
            "result": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
