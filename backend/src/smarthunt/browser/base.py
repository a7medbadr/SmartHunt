from dataclasses import dataclass


@dataclass(slots=True)
class JobResult:
    title: str
    company: str
    location: str
    source: str
    url: str
