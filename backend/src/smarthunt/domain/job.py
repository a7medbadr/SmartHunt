from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class DiscoveredJob:

    title: str

    company: str

    location: str

    source: str

    url: str | None

    description: str = ""

    requirements: str = ""

    # When the job was actually posted on the source site — distinct from
    # the DB row's created_at, which is when SmartHunt discovered it.
    # Optional: only LinkedIn's real provider currently extracts this
    # (its `.job-search-card__listdate` element); other providers leave
    # it unset until they're real too.
    posted_at: date | None = None
