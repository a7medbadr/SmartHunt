import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_limit: int = 100,
        window_seconds: int = 60,
    ):
        super().__init__(app)

        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)

    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        now = time.time()

        requests = self.clients[client_ip]

        requests[:] = [timestamp for timestamp in requests if now - timestamp < self.window_seconds]

        print(f"[RATE LIMIT] ip={client_ip} " f"count_before={len(requests)} " f"id={id(self)}")

        if len(requests) >= self.requests_limit:
            print("[RATE LIMIT] BLOCKED")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                },
            )

        requests.append(now)

        print(f"[RATE LIMIT] count_after={len(requests)}")

        return await call_next(request)
