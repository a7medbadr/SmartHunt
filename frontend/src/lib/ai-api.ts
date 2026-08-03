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
// retries automatically, up to 3 times = 270s worst case). 280s gives
// the frontend enough room to actually see even that worst case
// resolve instead of aborting first and showing a false "error, try
// again" while the backend was still working. Ollama calls are also
// now serialized backend-side (see ai/providers/ollama.py) so
// concurrent requests stop fighting each other for the same CPU-bound
// model, which was the main cause of attempts exceeding 90s at all.
const AI_REQUEST_TIMEOUT_MS = 280000;

export async function generateAIResponse(
  prompt: string,
  maxTokens?: number,
): Promise<AIGenerateResponse> {
  const { data } = await apiClient.post<AIGenerateResponse>(
    "/ai/generate",
    maxTokens ? { prompt, max_tokens: maxTokens } : { prompt },
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
