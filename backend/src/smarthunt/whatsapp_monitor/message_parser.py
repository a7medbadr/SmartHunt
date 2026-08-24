import re
from dataclasses import dataclass

from smarthunt.linkedin_monitor.relevance import is_job_related_post, synthesize_title
from smarthunt.matching.services.job_relevance import is_relevant_job_title

# The owner's WhatsApp job channels (e.g. "ELITE IT | وظائف تقنية معلومات -
# السعودية") post in a very consistent structured format:
#
#   📌 Job Opportunity | Senior Content Creator     (or "📌 فرصة وظيفية | ...")
#
#   🏢 Mindspire
#
#   📍 Riyadh, Saudi Arabia
#
#   🌟 Requirements: ...
#
# — confirmed live 2026-08-08 against real messages the owner pasted from
# the channel. This is far more reliably parseable than LinkedIn's free-
# text posts (linkedin_monitor/relevance.py's synthesize_title's "first
# non-boilerplate line" heuristic exists only because LinkedIn posts have
# no structure at all) — real title/company/location can be extracted
# directly instead of guessed at.
_TITLE_HEADER_PATTERN = re.compile(
    r"^\s*(?:📌\s*)?(?:job\s+opportunity|فرصة\s+وظيفية)\s*\|\s*(?P<title>.+?)\s*$",
    re.IGNORECASE,
)
_COMPANY_LINE_PATTERN = re.compile(r"^\s*🏢\s*(?P<company>.+?)\s*$")
_LOCATION_LINE_PATTERN = re.compile(r"^\s*📍\s*(?P<location>.+?)\s*$")

_MAX_TITLE_LENGTH = 200
_MAX_COMPANY_LENGTH = 255
_MAX_LOCATION_LENGTH = 255

_FALLBACK_COMPANY = "WhatsApp Channel"


@dataclass
class ParsedJobPost:
    title: str
    company: str
    location: str | None
    matched_structured_format: bool


def parse_job_message(text: str) -> ParsedJobPost:
    """Extracts title/company/location from the 📌/🏢/📍-structured format
    above. Falls back to synthesize_title (reused from
    linkedin_monitor.relevance) plus a generic company when a message
    doesn't match — needed for group chats, which likely aren't as
    consistently formatted as the ELITE IT channel."""
    title: str | None = None
    company: str | None = None
    location: str | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if title is None:
            match = _TITLE_HEADER_PATTERN.match(line)
            if match:
                title = match.group("title")[:_MAX_TITLE_LENGTH]
                continue

        if company is None:
            match = _COMPANY_LINE_PATTERN.match(line)
            if match:
                company = match.group("company")[:_MAX_COMPANY_LENGTH]
                continue

        if location is None:
            match = _LOCATION_LINE_PATTERN.match(line)
            if match:
                location = match.group("location")[:_MAX_LOCATION_LENGTH]
                continue

    if title is not None:
        return ParsedJobPost(
            title=title,
            company=company or _FALLBACK_COMPANY,
            location=location,
            matched_structured_format=True,
        )

    return ParsedJobPost(
        title=synthesize_title(text),
        company=_FALLBACK_COMPANY,
        location=location,
        matched_structured_format=False,
    )


# Duplicated (not imported) from linkedin_monitor/relevance.py's private
# _SAUDI_LOCATION_PATTERNS on purpose — same precedent as
# scheduler/jobs.py's DISCOVERY_LOCATION being duplicated in
# retry_worker.py: a handful of stable regexes, not worth a cross-module
# dependency on another package's private implementation detail.
_SAUDI_LOCATION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bsaudi\b",
        r"\briyadh\b",
        r"\bjeddah\b",
        r"\bdammam\b",
        r"\bkhobar\b",
        r"\bksa\b",
        r"السعودية",
        r"الرياض",
        r"جدة",
        r"الدمام",
        r"الخبر",
    )
]


def _has_saudi_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SAUDI_LOCATION_PATTERNS)


def is_job_related_message(text: str) -> bool:
    """A structured "Job Opportunity | ..." post from one of these
    channels already IS a real hiring announcement — unlike LinkedIn's
    free-text posts, there's no need to also require a generic hiring
    keyword (is_job_related_post's _HIRING_SIGNAL_PATTERNS look for
    phrases like "hiring"/"apply now" a structured post doesn't
    necessarily repeat). Still enforces the same Saudi-Arabia-only scope
    and relevant-tech-title bar the rest of discovery enforces. An
    unstructured message (e.g. from a group chat, not a channel) falls
    back to the full LinkedIn-post relevance check unchanged."""
    if not text:
        return False

    parsed = parse_job_message(text)
    if parsed.matched_structured_format:
        # Checked against the parsed title only, not the whole message —
        # same rationale as linkedin_monitor/relevance.py's identical
        # tightening: a structured message can legitimately list "Linux"
        # somewhere in its requirements for a role whose real title has
        # nothing to do with it, so the technology name has to appear in
        # the title itself, same bar every other job source is held to.
        return _has_saudi_signal(text) and is_relevant_job_title(parsed.title)

    return is_job_related_post(text)
