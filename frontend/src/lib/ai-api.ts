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

export async function generateAIResponse(
  prompt: string,
): Promise<AIGenerateResponse> {
  const { data } = await apiClient.post<AIGenerateResponse>("/ai/generate", {
    prompt,
  });
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
    { timeout: 120000 },
  );
  return data;
}
