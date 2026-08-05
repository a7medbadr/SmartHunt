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

// Backend per-attempt AI timeout for this call is 260s (see
// cover_letter/service.py), with up to ai_max_retries attempts before
// falling back to a template letter — 280s here used to be *shorter*
// than even a single backend attempt's own budget, so the client always
// gave up before the backend could ever finish or fall back, showing a
// generic error even on requests the backend would have completed.
// Needs real margin over retries * per-attempt timeout.
const COVER_LETTER_TIMEOUT_MS = 850000;

export async function generateCoverLetter(
  payload: GenerateCoverLetterPayload,
): Promise<GenerateCoverLetterResult> {
  const { data } = await apiClient.post<GenerateCoverLetterResult>(
    "/cover-letter/generate",
    payload,
    { timeout: COVER_LETTER_TIMEOUT_MS },
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
