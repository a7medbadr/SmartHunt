from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status


async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def unhandled_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal Server Error",
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
