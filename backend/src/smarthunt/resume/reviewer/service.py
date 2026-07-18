from smarthunt.resume.reviewer.schemas import ResumeReviewResponse


class ResumeReviewer:
    def review_resume(self, text: str) -> ResumeReviewResponse:
        content_lower = text.lower()
        strengths = []
        weaknesses = []
        recommendations = []

        # Simple rule-based logic (To be connected to LLM later)
        if "linux" in content_lower:
            strengths.append("Linux")
        if "docker" in content_lower:
            strengths.append("Docker")
        if "python" in content_lower:
            strengths.append("Python")

        if "aws" not in content_lower:
            weaknesses.append("No AWS")
            recommendations.append("Consider adding AWS cloud experience")
        if "terraform" not in content_lower:
            weaknesses.append("No Terraform")
            recommendations.append("Mention IaC tools like Terraform")

        if "achievement" in content_lower or "metric" in content_lower or "%" in content_lower:
            strengths.append("Quantified achievements present")
        else:
            recommendations.append("Add quantified achievements")

        # Base ATS score calculation
        base_score = 70
        score_bonus = len(strengths) * 5
        score_penalty = len(weaknesses) * 3
        ats_score = min(max(base_score + score_bonus - score_penalty, 0), 100)

        return ResumeReviewResponse(
            ats_score=ats_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
