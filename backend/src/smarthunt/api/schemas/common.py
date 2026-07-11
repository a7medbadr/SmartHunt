from pydantic import BaseModel


class Pagination(BaseModel):
    page: int = 1
    size: int = 20


class PageMeta(BaseModel):
    total: int
    page: int
    size: int
    pages: int
