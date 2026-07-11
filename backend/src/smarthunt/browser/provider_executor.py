import asyncio
import time

from smarthunt.browser.provider_result import ProviderExecution


class ProviderExecutor:

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    async def execute(self, provider, keyword, location=None):

        started = time.perf_counter()

        try:

            jobs = await asyncio.wait_for(
                provider.search(keyword, location),
                timeout=self.timeout,
            )

            return ProviderExecution(
                provider=provider.name,
                success=True,
                jobs=jobs,
                duration=time.perf_counter() - started,
            )

        except Exception as exc:

            return ProviderExecution(
                provider=provider.name,
                success=False,
                jobs=[],
                error=str(exc),
                duration=time.perf_counter() - started,
            )
