from smarthunt.matching.job_parser import extract_job_skills
from smarthunt.resume.parser.skills import extract_skills


def generate_resume(
    resume_text: str,
    job_description: str,
) -> dict:
    # 1. Extract skills from resume and job description
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_job_skills(job_description))

    # 2. Compute matched and missing skills
    matched = sorted(list(resume_skills.intersection(job_skills)))
    missing = sorted(list(job_skills.difference(resume_skills)))

    # 3. Calculate score
    score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

    # 4. Format skills for template display
    core_skills_str = "\n".join(f"- {skill.title()}" for skill in matched) if matched else "- N/A"
    recommended_skills_str = (
        "\n".join(f"- {skill.title()}" for skill in missing) if missing else "- None"
    )

    # 5. Build template-based resume
    generated_resume_template = f"""# Tailored Professional Resume

## Professional Summary
Experienced technical professional with demonstrated expertise aligned with job requirements.

## Core Skills
{core_skills_str}

## Recommended Learning & Gap Analysis
{recommended_skills_str}
""".strip()

    return {
        "score": score,
        "matched_skills": matched,
        "recommended_skills": missing,
        "generated_resume": generated_resume_template,
    }
