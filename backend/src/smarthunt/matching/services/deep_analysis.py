from smarthunt.ai.service import ai_service
from smarthunt.ai.types import AIRequest
from smarthunt.matching.services.matcher import match

DEEP_ANALYSIS_PROMPT = """You are a career advisor. Given a resume and a job description, reply \
ONLY in this exact Markdown structure. Write entirely in Arabic (no English, no Chinese). Do not \
repeat or quote the resume or job text. Keep it brief — one line per bullet, no extra commentary:

## ملخص
One sentence.

## استراتيجية التقديم
- point 1
- point 2

## أسئلة مقابلة متوقعة
1. question
2. question

## تحذيرات
One sentence, or "لا توجد" if none.

Resume: {resume}

Job: {job}
"""

# The local Ollama model is CPU-bound — prompt-eval time scales with input
# length. Confirmed live 2026-08-03/04: a resume+job prompt truncated to
# 3000 chars each (1690 tokens combined) took 237.6s end to end on an
# otherwise-idle host — already past the 115s timeout below, so every real
# attempt was being cancelled by asyncio.wait_for mid-generation and
# retried from scratch rather than allowed to finish. Halved so a single
# attempt has a real chance to complete within its budget. Only the prompt
# fed to the AI is truncated — match() below still scores against the full
# resume, so rule-based skill matching accuracy is unaffected.
_MAX_RESUME_CHARS_FOR_AI = 1500


def _truncate_for_ai(text: str) -> str:
    if len(text) <= _MAX_RESUME_CHARS_FOR_AI:
        return text
    return text[:_MAX_RESUME_CHARS_FOR_AI] + "\n...(تم اختصار باقي السيرة الذاتية)"


class DeepAnalysisResult:
    def __init__(
        self,
        score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        ai_summary: str,
        provider: str,
        success: bool,
    ):
        self.score = score
        self.matched_skills = matched_skills
        self.missing_skills = missing_skills
        self.ai_summary = ai_summary
        self.provider = provider
        self.success = success


async def generate_deep_analysis(resume: str, job: str) -> DeepAnalysisResult:
    rule_based = match(resume, job)

    ai_response = await ai_service.generate(
        AIRequest(
            prompt=DEEP_ANALYSIS_PROMPT.format(
                resume=_truncate_for_ai(resume), job=_truncate_for_ai(job)
            ),
            max_tokens=280,
            timeout=200.0,
        )
    )

    return DeepAnalysisResult(
        score=rule_based["score"],
        matched_skills=rule_based["matched_skills"],
        missing_skills=rule_based["missing_skills"],
        ai_summary=ai_response.content,
        provider=ai_response.provider.value,
        success=ai_response.success,
    )
