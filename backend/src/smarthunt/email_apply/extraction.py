import re

# Deliberately simple/conservative — good enough for "does this job
# posting/post text contain a real-looking contact email", not a full
# RFC 5322 validator.
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Common "noreply"/system addresses that show up in job descriptions
# (e.g. copied from an ATS footer) but aren't a real place to send a CV.
_IGNORED_LOCAL_PARTS = {"noreply", "no-reply", "donotreply", "do-not-reply"}


def extract_email(*texts: str | None) -> str | None:
    """Returns the first real-looking contact email found across the
    given text fields (e.g. a job's description + requirements), or
    None. Used to detect "apply by sending your CV to this address"
    postings, which many regional job boards and LinkedIn posts use
    instead of (or alongside) a structured Easy Apply form."""
    for text in texts:
        if not text:
            continue
        for match in _EMAIL_PATTERN.finditer(text):
            email = match.group(0)
            local_part = email.split("@", 1)[0].lower()
            if local_part in _IGNORED_LOCAL_PARTS:
                continue
            return email
    return None
