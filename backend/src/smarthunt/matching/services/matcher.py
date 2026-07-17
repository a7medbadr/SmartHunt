import re
from typing import Any, Dict, Set

SKILLS = [
    "python",
    "linux",
    "openshift",
    "docker",
    "kubernetes",
    "ansible",
    "git",
    "jenkins",
    "terraform",
    "aws",
    "azure",
    "vmware",
    "red hat",
    "aix",
]


def extract_skills(text: str) -> Set[str]:
    """Extract known skills from a given text string."""
    if not text:
        return set()

    normalized_text = text.lower()
    found_skills = set()

    for skill in SKILLS:
        # استخدام Word Boundary أو بحث صريح للـ Multi-word skills
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized_text):
            found_skills.add(skill)

    return found_skills


def match(resume_text: str, job_text: str) -> Dict[str, Any]:
    """Calculates matching percentage and skill gaps between resume and job description."""
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)

    # لو الوظيفة ملهاش أي مهارات مطلوبة محددة في القائمة
    if not job_skills:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

    matched_skills = sorted(list(job_skills.intersection(resume_skills)))
    missing_skills = sorted(list(job_skills - resume_skills))

    score = round((len(matched_skills) / len(job_skills)) * 100)

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }
