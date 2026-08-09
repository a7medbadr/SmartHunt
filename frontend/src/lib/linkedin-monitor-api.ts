import { apiClient } from "@/lib/api-client";

export interface MonitoredAccount {
  id: number;
  profile_url: string;
  label: string | null;
  enabled: boolean;
  last_checked_at: string | null;
  created_at: string;
}

export interface MonitoredHashtag {
  id: number;
  tag: string;
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
// isn't reported as failed. Raised again 2026-08-07 from 240000 (4 min)
// to 600000 (10 min) per explicit request for a bigger safety margin —
// the home feed's full 40-scroll-round scan targeting 50 posts already
// measured ~3m19s on a quiet host, and now does extra per-post work
// (post_scanner.py's "…more" expand-before-read fix) that can push a
// real run closer to the old ceiling on a loaded host. This one constant
// covers all three real LinkedIn scan actions (home feed, a single
// monitored account, a single hashtag) uniformly, as requested — none of
// them should be tighter than the others. Comfortably inside the Next.js
// proxy's own 900000ms (15 min) ceiling (next.config.ts's
// experimental.proxyTimeout), so this is still the actual limiting
// timeout, not a dead setting shadowed by a shorter one upstream.
const SCAN_TIMEOUT_MS = 600000;

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

export async function scanAccountNow(id: number, signal?: AbortSignal): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    `/linkedin-monitor/accounts/${id}/scan`,
    undefined,
    { timeout: SCAN_TIMEOUT_MS, signal },
  );
  return data;
}

export async function scanHomeFeedNow(signal?: AbortSignal): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    "/linkedin-monitor/scan-feed",
    undefined,
    { timeout: SCAN_TIMEOUT_MS, signal },
  );
  return data;
}

// Hashtags moved 2026-08-06 from a hardcoded, read-only list to a real,
// owner-editable DB table — the below mirrors the monitored-accounts
// functions above exactly (add/list/enable/delete/scan-one), replacing
// the old listHashtags(): string[] + scanHashtagsNow(hashtags: string[])
// bulk pair.
export async function listHashtags(): Promise<MonitoredHashtag[]> {
  const { data } = await apiClient.get<MonitoredHashtag[]>("/linkedin-monitor/hashtags");
  return data;
}

export async function addHashtag(tag: string): Promise<MonitoredHashtag> {
  const { data } = await apiClient.post<MonitoredHashtag>("/linkedin-monitor/hashtags", { tag });
  return data;
}

export async function setHashtagEnabled(id: number, enabled: boolean): Promise<MonitoredHashtag> {
  const { data } = await apiClient.patch<MonitoredHashtag>(`/linkedin-monitor/hashtags/${id}`, {
    enabled,
  });
  return data;
}

export async function removeHashtag(id: number): Promise<void> {
  await apiClient.delete(`/linkedin-monitor/hashtags/${id}`);
}

export async function scanHashtagNow(id: number, signal?: AbortSignal): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    `/linkedin-monitor/hashtags/${id}/scan`,
    undefined,
    { timeout: SCAN_TIMEOUT_MS, signal },
  );
  return data;
}
