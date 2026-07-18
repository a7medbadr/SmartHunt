import re

KNOWN_SKILLS = [
    "linux",
    "python",
    "docker",
    "kubernetes",
    "openshift",
    "ansible",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "git",
    "jenkins",
    "prometheus",
    "grafana",
]


def extract_skills(text: str) -> list[str]:
    """Extract known skills from a text, preserving KNOWN_SKILLS order, no duplicates."""
    if not text:
        return []

    normalized_text = text.lower()
    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized_text):
            found_skills.append(skill)

    return found_skills
