import { apiClient } from "@/lib/api-client";

export interface ResumeInfo {
  uploaded: boolean;
  filename?: string;
  stored_path?: string;
  size?: number;
}

export async function getResume(): Promise<ResumeInfo> {
  const { data } = await apiClient.get<ResumeInfo>("/resume");
  return data;
}

export async function getResumeText(): Promise<string | null> {
  const { data } = await apiClient.get<{ text: string | null }>("/resume/text");
  return data.text;
}

export async function uploadResume(file: File): Promise<unknown> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post("/resume/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteResume(): Promise<unknown> {
  const { data } = await apiClient.delete("/resume");
  return data;
}

export interface ResumeAnalysis {
  skills: string[];
}

export async function analyzeResume(file: File): Promise<ResumeAnalysis> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<ResumeAnalysis>("/resume/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export interface TailoredResume {
  job_id: number;
  summary: string;
  generated_text: string;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  updated_at: string;
}

// Backend per-attempt AI timeout for this call is 220s (see
// resume/services/tailoring.py), with up to ai_max_retries attempts before
// falling back — 280s here used to be *shorter* than even a single
// backend attempt's own budget, so the client gave up before the backend
// could ever finish or fall back. Needs real margin over
// retries * per-attempt timeout, not just over one attempt.
const TAILORED_RESUME_TIMEOUT_MS = 700000;

export async function generateTailoredResumeForJob(jobId: number): Promise<TailoredResume> {
  const { data } = await apiClient.post<TailoredResume>(
    `/resume/tailored/${jobId}`,
    undefined,
    { timeout: TAILORED_RESUME_TIMEOUT_MS },
  );
  return data;
}

export async function getTailoredResumeForJob(jobId: number): Promise<TailoredResume | null> {
  try {
    const { data } = await apiClient.get<TailoredResume>(`/resume/tailored/${jobId}`);
    return data;
  } catch (err) {
    const status = (err as { response?: { status?: number } }).response?.status;
    if (status === 404) return null;
    throw err;
  }
}
