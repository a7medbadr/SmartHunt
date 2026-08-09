import { apiClient } from "@/lib/api-client";
import { translations, type Locale } from "@/lib/i18n/translations";

export interface AIGenerateRequest {
  prompt: string;
}

export interface AIGenerateResponse {
  content: string;
  provider: string;
  success: boolean;
  error: string | null;
}

// Measured live 2026-08-04 on an otherwise-idle host: a resume+job prompt
// truncated to 3000 chars each (1690 tokens combined) took 237.6s end to
// end against the configured local model — already past a 150s
// per-attempt timeout, so asyncio.wait_for on the backend was cancelling
// a genuinely-in-progress, would-have-succeeded generation and retrying
// from scratch every time (up to 3x) before ever falling back. 260s per
// attempt (with the halved MAX_RESUME_CHARS_FOR_AI below) gives a single
// real attempt real margin to finish. The client-side timeout has to
// cover the full retries * per-attempt-timeout worst case with margin —
// a long wait, but the progress indicator on these actions makes that
// bearable instead of looking frozen.
const AI_REQUEST_TIMEOUT_MS = 850000;
const AI_SERVER_TIMEOUT_SECONDS = 260;

// Halved 2026-08-04 (from 3000) after the measurement above — cuts
// prompt-eval time roughly in half, which is what actually let a single
// attempt finish inside its timeout budget instead of always being
// cancelled and retried. A well-structured resume front-loads what
// matters (summary, skills, most recent role) in its first portion, so
// truncating there keeps answers useful while cutting inference time
// substantially.
const MAX_RESUME_CHARS_FOR_AI = 1500;

export function truncateResumeForAI(resume: string, locale: Locale = "ar"): string {
  return resume.length > MAX_RESUME_CHARS_FOR_AI
    ? resume.slice(0, MAX_RESUME_CHARS_FOR_AI) + translations[locale].aiPrompts.resumeTruncatedNote
    : resume;
}

// A job description can be just as long as a resume — unbounded here
// before, so an interview-prep call against a long real posting could
// blow past the timeout budget the same way an untruncated resume did.
function truncateJobForAI(job: string, locale: Locale = "ar"): string {
  return job.length > MAX_RESUME_CHARS_FOR_AI
    ? job.slice(0, MAX_RESUME_CHARS_FOR_AI) + translations[locale].aiPrompts.jobTruncatedNote
    : job;
}

export async function generateAIResponse(
  prompt: string,
  maxTokens?: number,
): Promise<AIGenerateResponse> {
  const { data } = await apiClient.post<AIGenerateResponse>(
    "/ai/generate",
    {
      prompt,
      ...(maxTokens ? { max_tokens: maxTokens } : {}),
      timeout: AI_SERVER_TIMEOUT_SECONDS,
    },
    { timeout: AI_REQUEST_TIMEOUT_MS },
  );
  return data;
}

export async function generateInterviewPrep(
  resume: string,
  job: string,
  locale: Locale = "ar",
): Promise<AIGenerateResponse> {
  const t = translations[locale].aiPrompts;
  const prompt =
    `${t.myResumeLabel}:\n\n${truncateResumeForAI(resume, locale)}\n\n---\n\n${t.jobDescriptionLabel}:\n\n${truncateJobForAI(job, locale)}\n\n---\n\n` +
    t.interviewPrepInstruction;

  const { data } = await apiClient.post<AIGenerateResponse>(
    "/ai/generate",
    { prompt, max_tokens: 400, timeout: AI_SERVER_TIMEOUT_SECONDS },
    { timeout: AI_REQUEST_TIMEOUT_MS },
  );
  return data;
}
