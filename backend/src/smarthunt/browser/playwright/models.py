from enum import Enum

from pydantic import BaseModel


class EngineStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    STOPPED = "STOPPED"


class OpenJobResult(BaseModel):
    status: str
    title: str | None = None


class DetectFormResult(BaseModel):
    available: bool
    easy_apply: bool = False
    selector: str | None = None
