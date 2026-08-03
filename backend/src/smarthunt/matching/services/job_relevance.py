import re

# The owner's real, narrow skill set — see CLAUDE.md's discovery section.
# LinkedIn's own search broadens "Linux Administrator"/"OpenShift
# Administrator"/etc. queries semantically (Systems Engineer, Network
# Security Engineer, SAP consultant, fire-alarm systems...), so a query
# match alone is not a relevance signal — the title itself must name one
# of the actual technologies.
_RELEVANT_TITLE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\blinux\b",
        r"\baix\b",
        r"\bopenshift\b",
        r"\bvmware\b",
        r"\bvsphere\b",
        r"\besxi\b",
        r"\bvcf\b",
        r"\bred\s*hat\b",
        r"\brhel\b",
        r"\bsan\b",
        r"\bnas\b",
        r"\bstorage\b",
    )
]

# A title can name a relevant technology and still be the wrong job —
# a different seniority/specialty this owner isn't targeting, or (per
# explicit instruction 2026-08-03) a posting restricted to Saudi
# nationals, which the owner (iqama holder, not a Saudi national)
# cannot apply to at all.
_EXCLUDED_TITLE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bmanager\b",
        r"\barchitect\b",
        r"\bdirector\b",
        r"\bhead\s+of\b",
        r"\bvice\s+president\b",
        r"\bchief\b",
        r"\bsaudi\s+national",
        r"\bnational(?:s)?\s+only\b",
        r"\bdatabase\s+administrator\b",
        r"\bdba\b",
    )
]


def is_relevant_job_title(title: str) -> bool:
    """Strict allow/deny check applied to discovered job titles — see
    CLAUDE.md's discovery scope notes. Only a title that actually names
    one of the owner's real technologies, and isn't excluded (wrong
    seniority/specialty, or nationality-restricted), passes."""
    if not title:
        return False
    if any(pattern.search(title) for pattern in _EXCLUDED_TITLE_PATTERNS):
        return False
    return any(pattern.search(title) for pattern in _RELEVANT_TITLE_PATTERNS)
