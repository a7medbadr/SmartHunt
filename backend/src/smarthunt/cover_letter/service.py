from smarthunt.ai.service import ai_service
from smarthunt.ai.types import AIRequest
from smarthunt.cover_letter.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
)
from smarthunt.matching.services.matcher import match

COVER_LETTER_PROMPT = """You are an expert career coach writing a job application cover letter.
Write a complete, professional, specific cover letter (180-250 words) for this candidate applying \
to this exact job. Use only real details from the resume below — do not invent experience. \
Reference the hiring company/team by name if it appears in the job description (say "your team" \
or "your organization" if no name is given). Mention at least one concrete, measurable achievement \
or piece of relevant experience from the resume, not just a list of skill names. Open with "Dear \
Hiring Manager," and close with a professional sign-off. Output only the letter text, in English, \
no headers, no explanation, no markdown.

Resume:
{resume}

Job description:
{job}
"""

FALLBACK_LETTER = (
    "Dear Hiring Manager,\n\n"
    "I am excited to apply for this position. My background includes {skills}, "
    "and I believe my experience aligns well with your team's needs. "
    "I would welcome the opportunity to discuss how I can contribute.\n\n"
    "Best regards"
)


class CoverLetterService:
    async def generate_cover_letter(
        self, request: CoverLetterGenerateRequest
    ) -> CoverLetterGenerateResponse:
        match_result = match(resume_text=request.resume, job_text=request.job)

        score = match_result["score"]
        matched_skills = match_result["matched_skills"]

        try:
            ai_response = await ai_service.generate(
                AIRequest(
                    prompt=COVER_LETTER_PROMPT.format(resume=request.resume, job=request.job),
                    max_tokens=500,
                    timeout=90.0,
                )
            )
            letter_content = ai_response.content.strip()
        except Exception:
            letter_content = ""

        if not letter_content:
            skills_text = (
                ", ".join(matched_skills) if matched_skills else "relevant technical skills"
            )
            letter_content = FALLBACK_LETTER.format(skills=skills_text)

        return CoverLetterGenerateResponse(
            score=score,
            matched_skills=matched_skills,
            generated_cover_letter=letter_content,
        )
