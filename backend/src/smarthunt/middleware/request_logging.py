import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("smarthunt")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # توليد وحفظ الـ Request ID داخل الـ state لتسهيل الوصول إليه في أي مكان
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # تسجيل تفاصيل الطلب الوارد مع الـ ID
        logger.info(
            f"Incoming request: {request.method} {request.url.path} [Request ID: {request_id}]"
        )

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # تسجيل تفاصيل الرد ووقت المعالجة
            logger.info(
                f"Completed request: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Process Time: {process_time:.2f}ms"
            )
            # إضافة الـ ID إلى الـ Headers الخاصة بالرد
            response.headers["X-Request-ID"] = request.state.request_id
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Failed request: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Process Time: {process_time:.2f}ms"
            )
            raise e
