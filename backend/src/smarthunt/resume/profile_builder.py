import re

from smarthunt.domain import ResumeProfile


class ResumeProfileBuilder:
    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{7,}\d")
    LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/[^\s]+", re.I)
    GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/[^\s]+", re.I)
    YEARS_RE = re.compile(
        r"(\d+(?:\.\d+)?)\+?\s+years?(?:\s+of\s+experience)?",
        re.I,
    )

    SKILLS = [
        "python",
        "java",
        "golang",
        "linux",
        "rhel",
        "openshift",
        "docker",
        "kubernetes",
        "ansible",
        "terraform",
        "aws",
        "azure",
        "gcp",
        "sql",
        "postgresql",
        "git",
    ]

    def build(self, text: str) -> ResumeProfile:
        profile = ResumeProfile()

        if not text:
            return profile

        if m := self.EMAIL_RE.search(text):
            profile.email = m.group(0)

        if m := self.PHONE_RE.search(text):
            profile.phone = m.group(0).strip()

        if m := self.LINKEDIN_RE.search(text):
            profile.linkedin = m.group(0)

        if m := self.GITHUB_RE.search(text):
            profile.github = m.group(0)

        if m := self.YEARS_RE.search(text):
            profile.years_of_experience = float(m.group(1))

        lower = text.lower()

        for skill in self.SKILLS:
            if skill in lower:
                profile.skills.append(skill)

        return profile


resume_profile_builder = ResumeProfileBuilder()
