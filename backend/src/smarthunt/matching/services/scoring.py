from difflib import SequenceMatcher


def calculate_score(
    resume: str,
    job_description: str,
) -> float:

    return round(
        SequenceMatcher(
            None,
            resume.lower(),
            job_description.lower(),
        ).ratio() * 100,
        2,
    )
