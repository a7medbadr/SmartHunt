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

# Measured live 2026-08-04 on an otherwise-idle host: a real resume+job
# prompt truncated to 3000 chars each (6262 chars / 1690 tokens total)
# took 237.6s end to end (88.5s prompt-eval + 146.5s generating 290
# tokens) against the configured local model — already past the 150s
# per-attempt timeout below, so asyncio.wait_for was cancelling a
# genuinely-in-progress, would-have-succeeded generation and retrying
# from scratch every time, up to 3x (450s+) before ever reaching the
# LOCAL fallback. Halving the truncation cuts prompt-eval roughly in
# half; the timeout below is raised to match with real margin.
_MAX_CHARS_FOR_AI = 1500


def _truncate_for_ai(text: str) -> str:
    if len(text) <= _MAX_CHARS_FOR_AI:
        return text
    return text[:_MAX_CHARS_FOR_AI] + "\n...(تم اختصار الباقي)"


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
                    prompt=COVER_LETTER_PROMPT.format(
                        resume=_truncate_for_ai(request.resume),
                        job=_truncate_for_ai(request.job),
                    ),
                    max_tokens=350,
                    # See _MAX_CHARS_FOR_AI comment above — 260s gives a
                    # single real attempt (measured ~150-200s for a
                    # halved, 1500-char-each prompt) enough room to
                    # actually finish instead of being cancelled by
                    # asyncio.wait_for mid-generation and retried from
                    # scratch.
                    timeout=260.0,
                )
            )
            letter_content = ai_response.content.strip()
            if ai_response.provider.value == "local":
                # The real providers all failed/timed out — the LOCAL
                # fallback isn't a real model, it's a stub that just
                # echoes the prompt back. That's worse than our own
                # simple template, not a usable letter.
                letter_content = ""
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
