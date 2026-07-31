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
