import { apiClient } from "@/lib/api-client";

export interface SchedulerHistoryEntry {
  id: number;
  provider: string;
  started_at: string;
  finished_at: string | null;
  status: string;
  jobs_found: number;
  message: string | null;
}

export async function listSchedulerHistory(): Promise<SchedulerHistoryEntry[]> {
  const { data } = await apiClient.get<SchedulerHistoryEntry[]>("/scheduler/history");
  return data;
}

export interface SchedulerLock {
  id: number;
  job_id: string;
  owner_id: string;
  acquired_at: string;
  expires_at: string;
}

export async function listSchedulerLocks(): Promise<SchedulerLock[]> {
  const { data } = await apiClient.get<SchedulerLock[]>("/scheduler/locks");
  return data;
}

export interface FailedSchedulerJob {
  id: number;
  provider: string;
  job_reference: string;
  status: string;
  retry_count: number;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export async function listFailedSchedulerJobs(): Promise<FailedSchedulerJob[]> {
  const { data } = await apiClient.get<FailedSchedulerJob[]>("/scheduler/failed-jobs");
  return data;
}

export interface DiscoveryRunResult {
  providers: number;
  discovered: number;
  inserted: number;
  duplicates: number;
}

export async function runDiscovery(
  query: string,
  location?: string,
): Promise<DiscoveryRunResult> {
  const { data } = await apiClient.post<DiscoveryRunResult>(
    "/discovery/run",
    null,
    { params: { query, location } },
  );
  return data;
}
