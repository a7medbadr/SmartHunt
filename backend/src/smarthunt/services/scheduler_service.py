from apscheduler.triggers.interval import IntervalTrigger

from smarthunt.scheduler import scheduler
from smarthunt.scheduler.jobs import (
    discover_devops,
    discover_linux,
    discover_python,
)


class SchedulerService:
    def start(self):
        scheduler.add_job(
            discover_python,
            IntervalTrigger(hours=1),
            id="python",
            replace_existing=True,
        )

        scheduler.add_job(
            discover_linux,
            IntervalTrigger(hours=2),
            id="linux",
            replace_existing=True,
        )

        scheduler.add_job(
            discover_devops,
            IntervalTrigger(hours=3),
            id="devops",
            replace_existing=True,
        )

        scheduler.start()
