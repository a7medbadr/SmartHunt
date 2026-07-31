from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from smarthunt.shared.observability.context import request_id


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        incoming_id = request.headers.get("X-Request-ID")

        rid = incoming_id or str(uuid4())

        request.state.request_id = rid
        request_id.set(rid)

        response = await call_next(request)

        response.headers["X-Request-ID"] = rid
        response.headers["X-Correlation-ID"] = rid

        return response
