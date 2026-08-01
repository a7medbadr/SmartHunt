import { apiClient } from "@/lib/api-client";

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string | null;
  source: string | null;
  url: string | null;
  description: string | null;
  requirements: string | null;
  created_at: string;
  score?: number | null;
}

export interface SearchResult {
  jobs: Job[];
  total: number;
  page: number;
  limit: number;
}

export interface SearchParams {
  keyword?: string;
  location?: string;
  source?: string;
  sort?: string;
  order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export async function searchJobs(params: SearchParams): Promise<SearchResult> {
  const { data } = await apiClient.get<SearchResult>("/search/jobs", { params });
  return data;
}

export async function getJob(id: number): Promise<Job> {
  const { data } = await apiClient.get<Job>(`/jobs/${id}`);
  return data;
}

export interface Favorite {
  id: number;
  job_id: number;
}

export async function listFavorites(): Promise<Favorite[]> {
  const { data } = await apiClient.get<Favorite[]>("/favorites");
  return data;
}

export async function addFavorite(jobId: number): Promise<Favorite> {
  const { data } = await apiClient.post<Favorite>("/favorites", { job_id: jobId });
  return data;
}

export async function removeFavorite(jobId: number): Promise<void> {
  await apiClient.delete(`/favorites/${jobId}`);
}

export interface JobNote {
  id: number;
  job_id: number;
  note: string;
  created_at: string;
  updated_at: string;
}

export async function listJobNotes(jobId: number): Promise<JobNote[]> {
  const { data } = await apiClient.get<JobNote[]>(`/job-notes/${jobId}`);
  return data;
}

export async function createJobNote(jobId: number, note: string): Promise<JobNote> {
  const { data } = await apiClient.post<JobNote>("/job-notes", { job_id: jobId, note });
  return data;
}

export async function deleteJobNote(noteId: number): Promise<void> {
  await apiClient.delete(`/job-notes/${noteId}`);
}

export interface JobTag {
  id: number;
  job_id: number;
  tag: string;
  created_at: string;
}

export async function listJobTags(jobId: number): Promise<JobTag[]> {
  const { data } = await apiClient.get<JobTag[]>(`/job-tags/${jobId}`);
  return data;
}

export async function addJobTag(jobId: number, tag: string): Promise<JobTag> {
  const { data } = await apiClient.post<JobTag>("/job-tags", { job_id: jobId, tag });
  return data;
}

export async function deleteJobTag(tagId: number): Promise<void> {
  await apiClient.delete(`/job-tags/${tagId}`);
}
