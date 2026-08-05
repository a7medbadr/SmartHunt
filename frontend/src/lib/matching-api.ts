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
  // The backend's own AI timeout for this call is 200s per attempt (see
  // matching/services/deep_analysis.py), with up to ai_max_retries
  // attempts on the real (CPU-bound, sometimes slow) local Ollama model —
  // 350s here used to be shorter than even 2 backend attempts, so the
  // frontend would abort before the backend could ever finish or fall
  // back. Needs real margin over retries * per-attempt timeout.
  const { data } = await apiClient.post<DeepAnalysisResult>(
    "/matching/deep-analysis",
    { resume, job },
    { timeout: 650000 },
  );
  return data;
}
