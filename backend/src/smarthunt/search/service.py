from typing import Optional
from smarthunt.database.repositories.job_repository import JobRepository


class SearchService:
    def __init__(self, job_repo: Optional[JobRepository] = None):
        self.job_repo = job_repo or JobRepository()


search_service = SearchService()
