from smarthunt.cover_letter.reviewer.schemas import CoverLetterReviewResponse


class CoverLetterReviewer:
    def review_cover_letter(self, text: str) -> CoverLetterReviewResponse:
        content_lower = text.lower()
        issues = []
        recommendations = []
        score = 85

        # Rule-based logic
        if len(text.strip().split()) < 50:
            issues.append("Too short")
            recommendations.append("Expand on your achievements and motivations")
            score -= 15

        company_keywords = ["company", "team", "organization", "inc", "ltd", "corp"]
        if not any(kw in content_lower for kw in company_keywords):
            issues.append("No company mention")
            recommendations.append("Mention the target company name explicitly")
            score -= 10

        if "dear" not in content_lower and "hiring manager" not in content_lower:
            issues.append("Missing formal salutation")
            recommendations.append("Add a formal greeting like 'Dear Hiring Manager'")
            score -= 5

        if "%" not in content_lower and "achieved" not in content_lower:
            issues.append("Too generic")
            recommendations.append("Mention specific measurable achievements")
            score -= 10

        score = max(0, min(100, score))

        return CoverLetterReviewResponse(
            score=score,
            issues=issues,
            recommendations=recommendations,
        )
