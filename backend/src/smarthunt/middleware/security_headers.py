from starlette.middleware.base import BaseHTTPMiddleware

from smarthunt.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if (
            request.url.path.startswith("/docs")
            or request.url.path.startswith("/redoc")
            or request.url.path.startswith("/openapi.json")
        ):
            if "Content-Security-Policy" in response.headers:
                del response.headers["Content-Security-Policy"]

            if "Strict-Transport-Security" in response.headers:
                del response.headers["Strict-Transport-Security"]

            return response

        if settings.security_headers_enabled:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self';"
            )

        return response
