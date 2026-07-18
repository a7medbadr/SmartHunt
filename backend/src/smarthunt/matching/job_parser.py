import re
from smarthunt.resume.parser.skills import KNOWN_SKILLS

# إضافة التقنيات الجديدة المحددة للسبرينت
JOB_ADDITIONAL_SKILLS = {
    "c++", "c#", "java", "go", "rust", "sql", "postgresql", "oracle",
    "mongodb", "redis", "kafka", "rabbitmq", "helm", "gitlab", "github",
    "ci/cd", "vmware", "rhel", "aix"
}

ALL_JOB_SKILLS = set(KNOWN_SKILLS).union(JOB_ADDITIONAL_SKILLS)


def extract_job_skills(text: str) -> list[str]:
    """Extract known technical skills from a job description text."""
    if not text or not text.strip():
        return []

    text_lower = text.lower()
    found_skills = set()

    for skill in ALL_JOB_SKILLS:
        skill_lower = skill.lower()
        # التعامل مع المهارات التي تحتوي على رموز مثل c++, c#, ci/cd
        escaped_skill = re.escape(skill_lower)
        pattern = rf"(?:\b|(?<=\W)){escaped_skill}(?:\b|(?=\W))"
        if re.search(pattern, text_lower):
            found_skills.add(skill_lower)

    return sorted(list(found_skills))
