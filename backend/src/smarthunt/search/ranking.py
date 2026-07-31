class RankingEngine:
    @staticmethod
    def calculate_match(job) -> tuple[float, dict]:
        score = 60.0
        details = {
            "skill_match": 70,
            "keyword_match": 65,
            "experience_match": 80,
            "education_match": 90,
            "missing_skills": ["Ansible Tower", "CI/CD Pipeline"],
            "bonus_skills": ["FastAPI", "OpenShift"],
        }
        title_lower = job.title.lower()
        if "senior" in title_lower or "admin" in title_lower:
            score += 15.0
        if job.remote:
            score += 10.0
        if job.salary and int(job.salary) >= 14000:
            score += 15.0
        return min(score, 100.0), details

    @classmethod
    def rank_jobs(cls, jobs: list) -> list:
        ranked = []
        for job in jobs:
            score, details = cls.calculate_match(job)
            ranked.append((job, score, details))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
