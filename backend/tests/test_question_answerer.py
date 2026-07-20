from smarthunt.browser.question_answerer import (
    Decision,
    QuestionAnswerer,
)
from smarthunt.domain import ResumeProfile


def test_answer_email():
    profile = ResumeProfile(
        email="test@example.com"
    )

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "What is your email address?",
        profile,
    )

    assert result.decision == Decision.ANSWER
    assert result.answer == "test@example.com"
    assert result.confidence == 1.0


def test_answer_phone():
    profile = ResumeProfile(
        phone="+966500000000"
    )

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "Mobile number",
        profile,
    )

    assert result.decision == Decision.ANSWER
    assert result.answer == "+966500000000"
    assert result.confidence == 1.0


def test_answer_linkedin():
    profile = ResumeProfile(
        linkedin="https://linkedin.com/in/test"
    )

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "LinkedIn profile",
        profile,
    )

    assert result.decision == Decision.ANSWER
    assert result.answer == "https://linkedin.com/in/test"
    assert result.confidence == 1.0


def test_answer_experience():
    profile = ResumeProfile(
        years_of_experience=8
    )

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "Years of experience",
        profile,
    )

    assert result.decision == Decision.ANSWER
    assert result.answer == "8"
    assert result.confidence == 1.0


def test_answer_skills():
    profile = ResumeProfile(
        skills=[
            "python",
            "linux",
        ]
    )

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "Skills",
        profile,
    )

    assert result.decision == Decision.ANSWER
    assert result.answer == "python, linux"
    assert result.confidence == 1.0


def test_unknown_question():
    profile = ResumeProfile()

    answerer = QuestionAnswerer()

    result = answerer.answer(
        "Do you have security clearance?",
        profile,
    )

    assert result.decision == Decision.UNKNOWN
    assert result.answer is None
    assert result.confidence == 0.0
