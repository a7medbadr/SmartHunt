from dataclasses import dataclass

from smarthunt.domain.job import DiscoveredJob


@dataclass(slots=True)
class Job:
    """
    Backward-compatible provider job model.

    Existing providers can continue importing Job until the
    migration to DiscoveredJob is completed.
    """

    external_id: str = ""
    provider: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    salary: str | None = None
    remote: bool = False
    country: str | None = None
    city: str | None = None

    def to_domain(self) -> DiscoveredJob:
        return DiscoveredJob(
            title=self.title,
            company=self.company,
            location=self.location,
            source=self.provider,
            url=self.url,
            description=self.description,
        )


__all__ = [
    "Job",
    "DiscoveredJob",
]
