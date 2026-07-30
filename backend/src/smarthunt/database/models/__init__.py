from smarthunt.activity.models import Activity
from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.browser.session.models import BrowserSession
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.search_history import SearchHistory
from smarthunt.database.models.user import User
from smarthunt.favorites.models import FavoriteJob
from smarthunt.job_notes.models import JobNote
from smarthunt.job_tags.models import JobTag
from smarthunt.notifications.models import Notification
from smarthunt.providers.health.models import ProviderHealth
from smarthunt.saved_searches.models import SavedSearch
from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.locks.models import SchedulerLock
from smarthunt.settings.models import UserSettings
from smarthunt.audit.models import AuditLog
from smarthunt.events.models import EventLog


__all__ = [
    "Activity",
    "Application",
    "ApplyQueueItem",
    "BrowserSession",
    "FavoriteJob",
    "Job",
    "JobNote",
    "JobTag",
    "Notification",
    "ProviderHealth",
    "Resume",
    "SavedSearch",
    "SchedulerHistory",
    "SchedulerLock",
    "SearchHistory",
    "User",
    "UserSettings",
    "AuditLog",
    "EventLog",
]
