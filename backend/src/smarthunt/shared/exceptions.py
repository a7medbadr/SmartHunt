from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

import structlog

logger = structlog.get_logger("smarthunt")


async def http_exception_handler(request: Request, exc):

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    await logger.awarning(
        "http_exception",
        service="smarthunt-backend",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=str(exc.detail),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "path": request.url.path,
            "request_id": request_id,
        },
    )


async def unhandled_exception_handler(request: Request, exc):

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    await logger.aexception(
        "unhandled_exception",
        service="smarthunt-backend",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal Server Error",
            "path": request.url.path,
            "request_id": request_id,
        },
    )
