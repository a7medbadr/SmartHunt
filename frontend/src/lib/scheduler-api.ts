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

export interface SearchProviderResult {
  provider: string;
  found: number;
  inserted: number;
  duplicates: number;
}

// Real site navigation (LinkedIn et al.) — measured live 2026-08-04 at
// ~43s for the backend's default limit=15 (LinkedIn visits each job's
// own detail page for its description, ~4.3s/job); generous margin over
// that, same reasoning as linkedin-monitor-api.ts's SCAN_TIMEOUT_MS.
// Raised 2026-08-07 from 150000 (2.5 min) to 600000 (10 min) for the same
// bigger safety margin requested for the other job-search blocks.
const SEARCH_PROVIDER_TIMEOUT_MS = 600000;

export async function searchProvider(
  provider: string,
  query: string,
  location?: string,
  signal?: AbortSignal,
): Promise<SearchProviderResult> {
  const { data } = await apiClient.post<SearchProviderResult>(
    "/discovery/search-provider",
    null,
    { params: { provider, query, location }, timeout: SEARCH_PROVIDER_TIMEOUT_MS, signal },
  );
  return data;
}
