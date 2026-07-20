from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ResumeProfile:
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    current_title: str | None = None
    current_company: str | None = None

    years_of_experience: float | None = None

    country: str | None = None
    city: str | None = None
    nationality: str | None = None

    education: str | None = None

    skills: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    salary_expectation: str | None = None
    notice_period: str | None = None
    summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResumeProfile":
        return cls(**data)

    def merge(self, other: "ResumeProfile") -> "ResumeProfile":
        for name in self.__dataclass_fields__:
            current = getattr(self, name)
            incoming = getattr(other, name)

            if isinstance(current, list):
                existing = set(current)
                for item in incoming:
                    if item not in existing:
                        current.append(item)
                        existing.add(item)
                continue

            if current is None and incoming is not None:
                setattr(self, name, incoming)

        return self
