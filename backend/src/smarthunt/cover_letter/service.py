from smarthunt.cover_letter.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
)
from smarthunt.matching.services.matcher import match


class CoverLetterService:
    async def generate_cover_letter(
        self, request: CoverLetterGenerateRequest
    ) -> CoverLetterGenerateResponse:
        match_result = match(resume_text=request.resume, job_text=request.job)

        score = match_result["score"]
        matched_skills = match_result["matched_skills"]

        if matched_skills:
            skills_bullets = "\n".join(f"- {skill.title()}" for skill in matched_skills)
        else:
            skills_bullets = "- Technical expertise alignment with the role requirement"

        letter_content = (
            "Dear Hiring Manager,\n\n"
            "I am excited to apply for the position.\n\n"
            "My experience includes:\n"
            f"{skills_bullets}\n\n"
            "I believe my background aligns well with your requirements.\n\n"
            "Best Regards"
        )

        return CoverLetterGenerateResponse(
            score=score,
            matched_skills=matched_skills,
            generated_cover_letter=letter_content,
        )
