import { apiClient } from "@/lib/api-client";

export interface DeepAnalysisResult {
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  ai_summary: string;
  provider: string;
  success: boolean;
}

export async function deepAnalyzeJob(
  resume: string,
  job: string,
): Promise<DeepAnalysisResult> {
  // The backend's own AI timeout for this call is 115s per attempt, with
  // up to 3 retries on the real (CPU-bound, sometimes slow) local Ollama
  // model — give the frontend enough room to see a retry succeed instead
  // of aborting first and reporting a false failure. Ollama calls are
  // also now serialized backend-side (ai/providers/ollama.py) so
  // concurrent requests stop competing for the same CPU-bound model.
  const { data } = await apiClient.post<DeepAnalysisResult>(
    "/matching/deep-analysis",
    { resume, job },
    { timeout: 350000 },
  );
  return data;
}
