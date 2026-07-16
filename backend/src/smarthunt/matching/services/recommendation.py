from .scoring import calculate_score


def recommend(
    resume: str,
    jobs: list[dict],
) -> list[dict]:

    scored = []

    for job in jobs:

        score = calculate_score(
            resume,
            job["description"],
        )

        job["score"] = score

        scored.append(job)

    return sorted(
        scored,
        key=lambda x: x["score"],
        reverse=True,
    )
