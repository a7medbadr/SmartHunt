from dataclasses import dataclass


@dataclass(slots=True)
class DiscoveredJob:
    title: str
    company: str
    location: str
    source: str
    url: str
