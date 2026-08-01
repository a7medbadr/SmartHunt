import pytest

from smarthunt.matching.services.job_signals import detect_no_sponsorship


@pytest.mark.parametrize(
    "text",
    [
        "We are unable to sponsor visas for this role.",
        "No sponsorship available at this time.",
        "Applicants must be authorized to work in the US without sponsorship.",
        "This position does not sponsor employment visas.",
    ],
)
def test_detect_no_sponsorship_true(text):
    assert detect_no_sponsorship(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Great benefits and a friendly team.",
        "We sponsor relocation and visas for the right candidate.",
    ],
)
def test_detect_no_sponsorship_false(text):
    assert detect_no_sponsorship(text) is False
