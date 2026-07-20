from __future__ import annotations

from enum import Enum


class QuestionType(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


_KNOWN_KEYWORDS: tuple[str, ...] = (
    "email",
    "e-mail",
    "phone",
    "mobile",
    "telephone",
    "linkedin",
    "github",
    "git hub",
    "portfolio",
    "full name",
    "name",
    "current title",
    "job title",
    "position",
    "company",
    "current company",
    "experience",
    "years",
    "country",
    "city",
    "nationality",
    "notice",
    "salary",
    "skills",
    "languages",
    "summary",
)

_UNSUPPORTED_KEYWORDS: tuple[str, ...] = (
    "captcha",
    "signature",
    "upload a video",
    "record a video",
    "background check consent",
    "drug test",
)


def classify(question: str) -> QuestionType:
    normalized = " ".join(
        question.lower().strip().split()
    )

    if not normalized:
        return QuestionType.UNSUPPORTED

    if any(
        keyword in normalized
        for keyword in _UNSUPPORTED_KEYWORDS
    ):
        return QuestionType.UNSUPPORTED

    if any(
        keyword in normalized
        for keyword in _KNOWN_KEYWORDS
    ):
        return QuestionType.KNOWN

    return QuestionType.UNKNOWN
