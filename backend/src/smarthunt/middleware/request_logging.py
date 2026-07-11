import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("smarthunt")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # تسجيل تفاصيل الطلب الوارد
        logger.info(f"Incoming request: {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # تسجيل تفاصيل الرد ووقت المعالجة
            logger.info(
                f"Completed request: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Process Time: {process_time:.2f}ms"
            )
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Failed request: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Process Time: {process_time:.2f}ms"
            )
            raise e
