from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from smarthunt.browser.question_classifier import (
    QuestionType,
    classify,
)
from smarthunt.domain import ResumeProfile


class Decision(str, Enum):
    ANSWER = "ANSWER"
    UNKNOWN = "UNKNOWN"
    SKIP = "SKIP"


@dataclass(slots=True)
class QuestionDecision:
    decision: Decision
    answer: str | None = None
    confidence: float = 0.0
    reason: str = ""


class QuestionAnswerer:
    """
    Maps natural language questions to ResumeProfile values.

    This class is intentionally independent from Playwright,
    DOM, Locator, or browser logic.
    """

    def answer(
        self,
        question: str,
        profile: ResumeProfile,
    ) -> QuestionDecision:

        normalized = self._normalize(question)

        if not normalized:
            return QuestionDecision(
                decision=Decision.SKIP,
                reason="empty question",
            )

        if classify(question) is QuestionType.UNSUPPORTED:
            return QuestionDecision(
                decision=Decision.SKIP,
                reason="unsupported question type",
            )

        mapping = (
            ("email", profile.email),
            ("e-mail", profile.email),

            ("phone", profile.phone),
            ("mobile", profile.phone),
            ("telephone", profile.phone),

            ("linkedin", profile.linkedin),

            ("github", profile.github),
            ("git hub", profile.github),

            ("portfolio", profile.portfolio),

            ("full name", profile.full_name),
            ("name", profile.full_name),

            ("current title", profile.current_title),
            ("job title", profile.current_title),
            ("position", profile.current_title),

            ("company", profile.current_company),
            ("current company", profile.current_company),

            ("experience", self._experience(profile)),
            ("years", self._experience(profile)),

            ("country", profile.country),
            ("city", profile.city),
            ("nationality", profile.nationality),

            ("notice", profile.notice_period),
            ("salary", profile.salary_expectation),

            ("skills", self._join(profile.skills)),
            ("languages", self._join(profile.languages)),

            ("summary", profile.summary),
        )

        for keyword, value in mapping:
            if keyword in normalized:

                if value is None:
                    return QuestionDecision(
                        decision=Decision.UNKNOWN,
                        confidence=0.5,
                        reason=(
                            f"matched '{keyword}' but "
                            "profile value is missing"
                        ),
                    )

                return QuestionDecision(
                    decision=Decision.ANSWER,
                    answer=value,
                    confidence=1.0,
                    reason=f"matched keyword '{keyword}'",
                )

        return QuestionDecision(
            decision=Decision.UNKNOWN,
            confidence=0.0,
            reason="no keyword match",
        )

    @staticmethod
    def _normalize(question: str) -> str:
        return " ".join(
            question.lower().strip().split()
        )

    @staticmethod
    def _join(values: list[str]) -> str | None:
        if not values:
            return None

        return ", ".join(values)

    @staticmethod
    def _experience(
        profile: ResumeProfile,
    ) -> str | None:

        if profile.years_of_experience is None:
            return None

        value = profile.years_of_experience

        if float(value).is_integer():
            return str(int(value))

        return str(value)


question_answerer = QuestionAnswerer()
