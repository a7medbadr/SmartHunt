import time
import uuid
import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger("smarthunt")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        path = scope.get("path", "")
        method = scope.get("method", "")

        await logger.ainfo("Incoming request", method=method, path=path, request_id=request_id)

        start_time = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = (time.perf_counter() - start_time) * 1000

                await logger.ainfo(
                    "Request completed",
                    method=method,
                    path=path,
                    process_time_ms=f"{process_time:.2f}",
                    request_id=request_id,
                )

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000

            await logger.aerror(
                "Request failed",
                error=str(e),
                method=method,
                path=path,
                process_time_ms=f"{process_time:.2f}",
                request_id=request_id,
            )
            raise
