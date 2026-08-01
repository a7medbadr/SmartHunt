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
  const { data } = await apiClient.post<DeepAnalysisResult>(
    "/matching/deep-analysis",
    { resume, job },
    { timeout: 120000 },
  );
  return data;
}
