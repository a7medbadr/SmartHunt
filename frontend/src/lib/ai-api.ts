import { apiClient } from "@/lib/api-client";

export interface AIGenerateRequest {
  prompt: string;
}

export interface AIGenerateResponse {
  content: string;
  provider: string;
  success: boolean;
  error: string | null;
}

// The local Ollama model this runs on is CPU-bound and, under real load,
// slow enough that a single attempt can miss the backend's own 90s
// per-attempt timeout — confirmed live: one real request took a 90s
// timeout on attempt 1, then succeeded in 87s on attempt 2 (backend
// retries automatically). 240s gives the frontend enough room to
// actually see that retry succeed instead of aborting first and
// showing a false "error, try again" while the backend was still
// working.
const AI_REQUEST_TIMEOUT_MS = 240000;

export async function generateAIResponse(
  prompt: string,
): Promise<AIGenerateResponse> {
  const { data } = await apiClient.post<AIGenerateResponse>(
    "/ai/generate",
    { prompt },
    { timeout: AI_REQUEST_TIMEOUT_MS },
  );
  return data;
}

export async function generateInterviewPrep(
  resume: string,
  job: string,
): Promise<AIGenerateResponse> {
  const prompt =
    `سيرتي الذاتية:\n\n${resume}\n\n---\n\nوصف الوظيفة:\n\n${job}\n\n---\n\n` +
    "جهزني لمقابلة شخصية لهذه الوظيفة بالتحديد: اكتب 3 أسئلة تقنية متوقعة بناءً على متطلبات الوظيفة، " +
    "و3 أسئلة سلوكية (behavioral) متوقعة، ولكل سؤال نصيحة مختصرة للإجابة عليه بناءً على خبرتي في السيرة الذاتية.";

  const { data } = await apiClient.post<AIGenerateResponse>(
    "/ai/generate",
    { prompt, max_tokens: 700 },
    { timeout: AI_REQUEST_TIMEOUT_MS },
  );
  return data;
}
