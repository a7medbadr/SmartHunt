from fastapi import APIRouter

from smarthunt.scheduler import scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("")
async def get_scheduler_status():
    # استدعاء حالة الـ scheduler المستورد مباشرة
    is_running = scheduler.running
    return {
        "status": "running" if is_running else "stopped",
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ],
    }
