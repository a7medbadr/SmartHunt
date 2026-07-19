from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.search_history import SearchHistory
from smarthunt.database.models.user import User
from smarthunt.activity.models import Activity
from smarthunt.favorites.models import FavoriteJob
from smarthunt.saved_searches.models import SavedSearch
from smarthunt.job_notes.models import JobNote
from smarthunt.job_tags.models import JobTag

__all__ = [
    "Application",
    "Job",
    "Resume",
    "SearchHistory",
    "User",
    "Activity",
    "FavoriteJob",
    "SavedSearch",
    "JobNote",
    "JobTag",
]
