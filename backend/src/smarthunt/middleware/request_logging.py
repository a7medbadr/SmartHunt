import time
import uuid

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

from smarthunt.shared.observability.context import request_id

logger = structlog.get_logger("smarthunt")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        rid = scope.get("state", {}).get("request_id")

        if not rid:
            rid = str(uuid.uuid4())

        request_id.set(rid)

        path = scope.get("path", "")
        method = scope.get("method", "")

        start_time = time.perf_counter()

        await logger.ainfo(
            "request_started",
            service="smarthunt-backend",
            request_id=rid,
            method=method,
            path=path,
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = (time.perf_counter() - start_time) * 1000

                await logger.ainfo(
                    "request_completed",
                    service="smarthunt-backend",
                    request_id=rid,
                    method=method,
                    path=path,
                    status_code=message["status"],
                    response_time_ms=round(duration, 2),
                )

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_wrapper,
            )

        except Exception:
            logger.exception(
                "request_failed",
                service="smarthunt-backend",
                request_id=rid,
                method=method,
                path=path,
            )
            raise
