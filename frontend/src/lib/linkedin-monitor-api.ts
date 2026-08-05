import { apiClient } from "@/lib/api-client";

export interface MonitoredAccount {
  id: number;
  profile_url: string;
  label: string | null;
  enabled: boolean;
  last_checked_at: string | null;
  created_at: string;
}

export interface ScanResult {
  scanned: number;
  saved: number;
  job_ids: number[];
}

// Real LinkedIn navigation — measured live 2026-08-04 at 30-57s under
// normal conditions, but this shares the host with other real browser
// automation (discovery runs, etc.) that can slow a scan down well past
// that on a busier moment; a client-side timeout firing while the
// backend request is still genuinely running produces a false "حصل خطأ"
// even though the scan itself succeeds and the job still gets saved a
// few seconds later — raised with real margin so a slow-but-real scan
// isn't reported as failed.
const SCAN_TIMEOUT_MS = 240000;

// Hashtag scans loop through every given hashtag sequentially on the
// backend (~60-65s each, measured live 2026-08-04) — a handful of
// hashtags in one request easily exceeds SCAN_TIMEOUT_MS, so this gets
// its own, much longer budget instead.
const HASHTAG_SCAN_TIMEOUT_MS = 850000;

export async function listMonitoredAccounts(): Promise<MonitoredAccount[]> {
  const { data } = await apiClient.get<MonitoredAccount[]>("/linkedin-monitor/accounts");
  return data;
}

export async function addMonitoredAccount(payload: {
  profileUrl: string;
  label?: string;
}): Promise<MonitoredAccount> {
  const { data } = await apiClient.post<MonitoredAccount>("/linkedin-monitor/accounts", {
    profile_url: payload.profileUrl,
    label: payload.label || undefined,
  });
  return data;
}

export async function setMonitoredAccountEnabled(
  id: number,
  enabled: boolean,
): Promise<MonitoredAccount> {
  const { data } = await apiClient.patch<MonitoredAccount>(`/linkedin-monitor/accounts/${id}`, {
    enabled,
  });
  return data;
}

export async function removeMonitoredAccount(id: number): Promise<void> {
  await apiClient.delete(`/linkedin-monitor/accounts/${id}`);
}

export async function scanAccountNow(id: number): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    `/linkedin-monitor/accounts/${id}/scan`,
    undefined,
    { timeout: SCAN_TIMEOUT_MS },
  );
  return data;
}

export async function scanHomeFeedNow(): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    "/linkedin-monitor/scan-feed",
    undefined,
    { timeout: SCAN_TIMEOUT_MS },
  );
  return data;
}

export async function scanHashtagsNow(hashtags: string[]): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    "/linkedin-monitor/scan-hashtags",
    { hashtags },
    { timeout: HASHTAG_SCAN_TIMEOUT_MS },
  );
  return data;
}

export async function listHashtags(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>("/linkedin-monitor/hashtags");
  return data;
}
