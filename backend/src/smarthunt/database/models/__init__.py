from smarthunt.activity.models import Activity
from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.browser.session.models import BrowserSession
from smarthunt.browser.unknown_questions import UnknownQuestion
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.search_history import SearchHistory
from smarthunt.database.models.user import User
from smarthunt.email_apply.models import EmailMessage
from smarthunt.favorites.models import FavoriteJob
from smarthunt.idempotency.models import IdempotencyKey
from smarthunt.job_notes.models import JobNote
from smarthunt.job_tags.models import JobTag
from smarthunt.linkedin_monitor.models import MonitoredHashtag, MonitoredLinkedInAccount
from smarthunt.notifications.models import Notification
from smarthunt.whatsapp_monitor.models import MonitoredWhatsAppChat
from smarthunt.providers.health.models import ProviderHealth
from smarthunt.providers.settings.models import ProviderSetting
from smarthunt.resume.models import TailoredResume
from smarthunt.scheduler.failed_job import FailedSchedulerJob
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
    "EmailMessage",
    "FailedSchedulerJob",
    "FavoriteJob",
    "IdempotencyKey",
    "Job",
    "JobNote",
    "JobTag",
    "MonitoredHashtag",
    "MonitoredLinkedInAccount",
    "MonitoredWhatsAppChat",
    "Notification",
    "ProviderHealth",
    "ProviderSetting",
    "Resume",
    "SchedulerHistory",
    "SchedulerLock",
    "SearchHistory",
    "TailoredResume",
    "UnknownQuestion",
    "User",
    "UserSettings",
    "AuditLog",
    "EventLog",
]
