import { apiClient } from "@/lib/api-client";

export interface GenerateCoverLetterPayload {
  resume: string;
  job: string;
}

export interface GenerateCoverLetterResult {
  score: number;
  matched_skills: string[];
  generated_cover_letter: string;
}

export async function generateCoverLetter(
  payload: GenerateCoverLetterPayload,
): Promise<GenerateCoverLetterResult> {
  const { data } = await apiClient.post<GenerateCoverLetterResult>(
    "/cover-letter/generate",
    payload,
  );
  return data;
}

export interface ReviewCoverLetterResult {
  score: number;
  issues: string[];
  recommendations: string[];
}

export async function reviewCoverLetter(
  coverLetter: string,
): Promise<ReviewCoverLetterResult> {
  const { data } = await apiClient.post<ReviewCoverLetterResult>(
    "/cover-letter/review",
    { cover_letter: coverLetter },
  );
  return data;
}
