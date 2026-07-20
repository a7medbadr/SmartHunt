"""
Application custom exceptions.
"""

from fastapi import HTTPException


class JobPageNotFound(HTTPException):
    def __init__(self, detail: str = "Job page not found"):
        super().__init__(
            status_code=404,
            detail=detail,
        )


class ApplicationFormNotFound(HTTPException):
    def __init__(self, detail: str = "Application form not found"):
        super().__init__(
            status_code=404,
            detail=detail,
        )
