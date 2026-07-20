from smarthunt.browser.question_answerer import QuestionAnswerer
from smarthunt.domain import ResumeProfile


def test_answer_email():

    profile = ResumeProfile(
        email="test@example.com"
    )

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "What is your email address?",
        profile,
    ) == "test@example.com"


def test_answer_phone():

    profile = ResumeProfile(
        phone="+966500000000"
    )

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "Mobile number",
        profile,
    ) == "+966500000000"


def test_answer_linkedin():

    profile = ResumeProfile(
        linkedin="https://linkedin.com/in/test"
    )

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "LinkedIn profile",
        profile,
    ) == "https://linkedin.com/in/test"


def test_answer_experience():

    profile = ResumeProfile(
        years_of_experience=8
    )

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "Years of experience",
        profile,
    ) == "8"


def test_answer_skills():

    profile = ResumeProfile(
        skills=[
            "python",
            "linux",
        ]
    )

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "Skills",
        profile,
    ) == "python, linux"


def test_unknown_question():

    profile = ResumeProfile()

    answerer = QuestionAnswerer()

    assert answerer.answer(
        "Do you have security clearance?",
        profile,
    ) is None
