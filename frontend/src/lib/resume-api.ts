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
