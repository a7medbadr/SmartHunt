import re

_NO_SPONSORSHIP_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"no\s+sponsorship",
        r"not\s+(?:able|in\s+a\s+position)\s+to\s+sponsor",
        r"unable\s+to\s+sponsor",
        r"without\s+(?:visa\s+)?sponsorship",
        r"does\s+not\s+sponsor",
        r"no\s+visa\s+sponsorship",
        r"must\s+(?:already\s+)?(?:be\s+)?(?:hold|have)\s+(?:a\s+)?work\s+(?:permit|authorization)",
        r"must\s+be\s+authorized\s+to\s+work.{0,40}without\s+sponsorship",
    )
]


def detect_no_sponsorship(text: str) -> bool:
    """Best-effort scan for explicit no-visa-sponsorship language in a job
    posting. A miss (false negative) just means the badge doesn't show —
    it never blocks anything, so it's safe to be conservative."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _NO_SPONSORSHIP_PATTERNS)
