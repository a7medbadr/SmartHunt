from dataclasses import dataclass

@dataclass(slots=True)
class Job:
    external_id: str
    provider: str
    title: str
    company: str
    location: str
    url: str
    description: str
    salary: str | None = None
    remote: bool = False
    country: str | None = None
    city: str | None = None
