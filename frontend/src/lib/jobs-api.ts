import { apiClient } from "@/lib/api-client";

export type ReviewStatus = "applied" | "not_suitable";

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
  posted_at?: string | null;
  post_url?: string | null;
  score?: number | null;
  no_sponsorship_signal?: boolean;
  review_status?: ReviewStatus | null;
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
  // Excludes exact source(s) from the results (comma-separated for more
  // than one) — used to keep LinkedIn-post/WhatsApp-message-sourced jobs
  // out of the job-sites tab, which each have their own separate tab.
  excludeSource?: string;
  // The owner's own triage: "applied" | "not_suitable" | "none"
  // (unreviewed only). Omit for "all".
  reviewStatus?: string;
  sort?: string;
  order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export async function searchJobs(params: SearchParams): Promise<SearchResult> {
  const { excludeSource, reviewStatus, ...rest } = params;
  const { data } = await apiClient.get<SearchResult>("/search/jobs", {
    params: { ...rest, exclude_source: excludeSource, review_status: reviewStatus },
  });
  return data;
}

export async function getJob(id: number): Promise<Job> {
  const { data } = await apiClient.get<Job>(`/jobs/${id}`);
  return data;
}

export async function deleteJob(id: number): Promise<void> {
  await apiClient.delete(`/jobs/${id}`);
}

// Setting null clears the review status back to unreviewed — used to
// toggle a status off (click "applied" again to un-mark it).
export async function updateJobReviewStatus(
  id: number,
  reviewStatus: ReviewStatus | null,
): Promise<Job> {
  const { data } = await apiClient.patch<Job>(`/jobs/${id}/review-status`, {
    review_status: reviewStatus,
  });
  return data;
}

export interface Favorite {
  id: number;
  job_id: number;
  job: Job | null;
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
