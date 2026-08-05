import pytest
from unittest.mock import MagicMock

from smarthunt.browser.question_answerer import (
    Decision,
    QuestionAnswerer,
)
from smarthunt.browser.question_classifier import (
    QuestionType,
    classify,
)
from smarthunt.browser.unknown_questions import (
    DBUnknownQuestionRepository,
    InMemoryUnknownQuestionRepository,
    UnknownQuestionRecord,
)
from smarthunt.domain import ResumeProfile


def test_classify_known_question():
    assert classify("What is your email address?") == QuestionType.KNOWN


def test_classify_unknown_question():
    assert classify("Do you own a pet dinosaur?") == QuestionType.UNKNOWN


def test_classify_unsupported_question():
    assert classify("Please complete the CAPTCHA") == QuestionType.UNSUPPORTED


@pytest.mark.asyncio
async def test_repository_save_and_list():
    repo = InMemoryUnknownQuestionRepository()

    await repo.save(
        UnknownQuestionRecord(
            provider="linkedin",
            url="https://example.com/job/1",
            label="Do you own a pet dinosaur?",
            html="<div>...</div>",
            confidence=0.0,
        )
    )

    records = await repo.list()

    assert len(records) == 1
    assert records[0].provider == "linkedin"
    assert records[0].label == "Do you own a pet dinosaur?"


@pytest.mark.asyncio
async def test_repository_filters_by_provider():
    repo = InMemoryUnknownQuestionRepository()

    await repo.save(
        UnknownQuestionRecord(
            provider="linkedin",
            url="https://example.com/job/1",
            label="q1",
            html="",
        )
    )

    await repo.save(
        UnknownQuestionRecord(
            provider="bayt",
            url="https://example.com/job/2",
            label="q2",
            html="",
        )
    )

    linkedin_only = await repo.list(provider="linkedin")

    assert len(linkedin_only) == 1
    assert linkedin_only[0].label == "q1"


@pytest.mark.asyncio
async def test_db_repository_save_and_list_persists_across_instances():
    """Regression test: the singleton used to be in-memory only, losing
    every paused application's blocking question on restart — confirmed
    live 2026-08-03 this was still the case despite the vision doc's
    "pause and notify" goal. A fresh repository instance (simulating a
    new process) must still see records saved by a previous one."""
    repo = DBUnknownQuestionRepository()

    await repo.save(
        UnknownQuestionRecord(
            provider="linkedin",
            url="https://example.com/job/db-1",
            label="years of kubernetes experience",
            html="<div>...</div>",
            confidence=0.6,
        )
    )

    fresh_repo = DBUnknownQuestionRepository()
    records = await fresh_repo.list(provider="linkedin")

    assert any(r.url == "https://example.com/job/db-1" for r in records)


def test_question_decision_answer():
    answerer = QuestionAnswerer()

    decision = answerer.answer(
        "What is your email?",
        ResumeProfile(email="test@example.com"),
    )

    assert decision.decision == Decision.ANSWER
    assert decision.answer == "test@example.com"


def test_question_decision_unknown():
    answerer = QuestionAnswerer()

    decision = answerer.answer(
        "Do you own a pet dinosaur?",
        ResumeProfile(),
    )

    assert decision.decision == Decision.UNKNOWN


def test_question_decision_skip_on_unsupported():
    answerer = QuestionAnswerer()

    decision = answerer.answer(
        "Please complete the CAPTCHA",
        ResumeProfile(),
    )

    assert decision.decision == Decision.SKIP


@pytest.mark.asyncio
async def test_easy_apply_pauses_on_unknown_question(monkeypatch):

    from smarthunt.browser.playwright.easy_apply import (
        easy_apply_engine,
    )
    from smarthunt.browser.playwright import (
        form_filler as form_filler_module,
    )

    page = MagicMock()

    async def fake_fill_form(p, provider="linkedin", job_id=None):
        return {
            "status": "QUESTION_REQUIRED",
            "question": "years of kubernetes experience",
        }

    monkeypatch.setattr(
        form_filler_module.form_filler_engine,
        "fill_form",
        fake_fill_form,
    )

    result = await easy_apply_engine.run(page)

    assert result["status"] == "PAUSED_UNKNOWN_QUESTION"
    assert result["question"] == "years of kubernetes experience"
