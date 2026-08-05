import re

from smarthunt.matching.services.job_relevance import is_relevant_job_title

# LinkedIn posts are free text, not structured job postings — there's no
# clean "title" field to check the way DiscoveryService's real job-search
# results have. is_relevant_job_title's regexes are just plain text
# search, though, so reusing them against the WHOLE post body works the
# same way: it still requires an actual named technology (Linux, RHEL,
# OpenShift, ...) and still excludes Manager/Architect/Saudi-national-only
# language — same standing rules as CLAUDE.md's discovery scope notes.

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

# Signals that a post is actually announcing an open role (as opposed to
# e.g. celebrating a hire, congratulating someone, or discussing the job
# market generally) — mirrors the kind of keyword search the owner's
# earlier personal scripts (/home/badr/collect-emails) did by hand.
_HIRING_SIGNAL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bhiring\b",
        r"\bvacanc(?:y|ies)\b",
        r"\bjob\s+opening\b",
        r"\bwe(?:'|’)re\s+looking\s+for\b",
        r"\bapply\s+now\b",
        r"\bsend\s+(?:your\s+)?cv\b",
        r"\bsend\s+(?:your\s+)?resume\b",
        r"مطلوب",
        r"نبحث عن",
        r"وظيفة\s+شاغرة",
        r"فرصة\s+عمل",
        r"التقديم",
    )
]


# Two boundary shapes needed to fully split real hashtags: "Saudi|Jobs"
# (lowercase→uppercase, e.g. #SaudiJobs) and "KSA|Jobs" (an all-caps
# acronym followed by a capitalized word, e.g. #KSAJobs — the simpler
# lowercase→uppercase rule alone misses this since there's no lowercase
# letter immediately before the split point).
_CAMEL_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_ACRONYM_BOUNDARY = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


def _split_hashtag_words(text: str) -> str:
    """LinkedIn hashtags are written with no separators (#SaudiJobs,
    #HiringNow, #RiyadhJobs) — found live 2026-08-05 chasing a report
    that the hourly feed scan and the new hashtag-search feature were
    both coming back essentially empty despite real, on-topic posts
    clearly being in the feed. Every regex here uses \\b word
    boundaries, which do NOT fire between "Saudi" and "Jobs" inside
    "SaudiJobs" (no non-word character between them) — so a post whose
    ONLY hiring/location signal was a compound hashtag like #SaudiJobs,
    #RiyadhJobs, #KSAJobs, #HiringNow, or #HiringAlert (several of which
    are literally in the owner's own hashtag list) silently failed both
    _HIRING_SIGNAL_PATTERNS and _SAUDI_LOCATION_PATTERNS every time.
    Inserting a space at each lowercase/digit→uppercase transition before
    matching (matching only, not storage/display) turns "#SaudiJobs"
    into "#Saudi Jobs" so the existing \\b-based patterns work unchanged."""
    text = _CAMEL_CASE_BOUNDARY.sub(" ", text)
    return _ACRONYM_BOUNDARY.sub(" ", text)


def is_job_related_post(text: str) -> bool:
    """A post counts as a real, relevant job posting only if it (a)
    actually announces hiring/an opening, (b) names one of the owner's
    real technologies (and isn't excluded — Manager/Architect/Saudi-
    national-only), and (c) mentions a Saudi location — the same
    Saudi-Arabia-only scope the rest of discovery enforces. Requiring
    all three keeps this from matching e.g. a random post that merely
    mentions "Linux" in passing."""
    if not text:
        return False

    matchable_text = _split_hashtag_words(text)

    has_hiring_signal = any(pattern.search(matchable_text) for pattern in _HIRING_SIGNAL_PATTERNS)
    has_saudi_signal = any(pattern.search(matchable_text) for pattern in _SAUDI_LOCATION_PATTERNS)

    return has_hiring_signal and has_saudi_signal and is_relevant_job_title(matchable_text)


# Profile-scan post text (post_scanner._clean_post_text) still legitimately
# keeps the poster's own name and professional headline ahead of the real
# post body (unlike the boilerplate lines already stripped there) — found
# live 2026-08-05 that blindly taking the first line produced titles like
# "Tamer Omar, MBA, PMP" instead of the actual "🚨 HIRING – FULL STACK
# DEVELOPER 🚨" a few lines further down. A LinkedIn headline is reliably
# "|"-separated ("PM | Agile Coach | Scrum Master | ..."); a name line is
# 1-4 Capitalized Words optionally followed by ", CREDENTIALS" — skip both
# shapes rather than assume a fixed number of lines, since not every
# profile has both (or in that order).
_HEADLINE_LINE_PATTERN = re.compile(r"\|")
_NAME_LINE_PATTERN = re.compile(r"^[A-Z][a-zA-Z.'-]*(\s[A-Z][a-zA-Z.'-]*){0,3}(,.*)?$")
# A repost's still-imperfectly-cleaned second embedded name/headline can
# leave a single bare hashtag ("#KSA") on its own line — not useful as a
# title on its own, unlike a real title line that happens to contain a
# hashtag among other words.
_LONE_HASHTAG_LINE_PATTERN = re.compile(r"^#\w+$")
# A short leftover fragment (a stray connection-status word, an isolated
# short token some cleanup pass missed) makes a useless title even if it
# doesn't match a specific known-junk pattern above — real job-post
# opening lines are essentially never this short.
_MIN_TITLE_LINE_LENGTH = 8


def synthesize_title(text: str, max_length: int = 90) -> str:
    """Posts don't have a structured title — use the first line that
    doesn't look like the poster's own name/headline/other leftover
    boilerplate (or a truncated prefix of the raw text if every line
    does) as a display title for the Jobs tab."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if (
            _HEADLINE_LINE_PATTERN.search(line)
            or _NAME_LINE_PATTERN.match(line)
            or _LONE_HASHTAG_LINE_PATTERN.match(line)
            or len(line) < _MIN_TITLE_LINE_LENGTH
        ):
            continue
        return line[:max_length]

    if lines:
        return lines[0][:max_length]
    return text.strip()[:max_length] or "LinkedIn Post"
