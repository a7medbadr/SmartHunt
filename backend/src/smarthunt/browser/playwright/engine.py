from smarthunt.browser.playwright.models import EngineStatus


class PlaywrightEngine:
    """
    Mock automation engine. No real browser is launched yet — every method
    returns a canned response so the rest of the system (queue, worker, API)
    can be built and tested against a stable interface.
    """

    def __init__(self):
        self.status = EngineStatus.NOT_STARTED

    async def start(self) -> dict:
        self.status = EngineStatus.STARTED
        return {"status": "started"}

    async def stop(self) -> dict:
        self.status = EngineStatus.NOT_STARTED
        return {"status": "stopped"}

    async def login(self, provider: str) -> dict:
        return {"status": "SUCCESS", "provider": provider}

    async def open_job(self, url: str) -> dict:
        return {"status": "SUCCESS", "job_url": url}

    async def apply(self, job_url: str) -> dict:
        return {"status": "SUCCESS", "job_url": job_url}

    async def take_screenshot(self, path: str = "screenshots/test.png") -> dict:
        return {"path": path}


playwright_engine = PlaywrightEngine()
