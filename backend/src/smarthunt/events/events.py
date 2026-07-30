from smarthunt.events.base import BaseEvent


class JobCreatedEvent(BaseEvent):
    event_type: str = "JOB_CREATED"


class ApplicationSubmittedEvent(BaseEvent):
    event_type: str = "APPLICATION_SUBMITTED"


class ResumeGeneratedEvent(BaseEvent):
    event_type: str = "RESUME_GENERATED"


class ProviderFailureEvent(BaseEvent):
    event_type: str = "PROVIDER_FAILURE"
