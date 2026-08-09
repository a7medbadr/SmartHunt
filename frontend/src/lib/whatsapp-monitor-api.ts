import { apiClient } from "@/lib/api-client";

export interface MonitoredChat {
  id: number;
  chat_url: string;
  label: string;
  chat_type: "channel" | "group";
  enabled: boolean;
  last_checked_at: string | null;
  created_at: string;
}

export interface ScanResult {
  scanned: number;
  saved: number;
  job_ids: number[];
}

export interface WhatsAppLoginStatus {
  logged_in: boolean;
}

// Same real-automation timing margin as linkedin-monitor-api.ts's
// SCAN_TIMEOUT_MS: a WhatsApp Web scan shares the exact same browser/host
// contention risk (comfortably inside next.config.ts's 900000ms proxy
// ceiling).
const SCAN_TIMEOUT_MS = 600000;

export async function listChats(): Promise<MonitoredChat[]> {
  const { data } = await apiClient.get<MonitoredChat[]>("/whatsapp-monitor/chats");
  return data;
}

export async function addChat(payload: {
  chatUrl: string;
  label: string;
  chatType: "channel" | "group";
}): Promise<MonitoredChat> {
  const { data } = await apiClient.post<MonitoredChat>("/whatsapp-monitor/chats", {
    chat_url: payload.chatUrl,
    label: payload.label,
    chat_type: payload.chatType,
  });
  return data;
}

export async function setChatEnabled(id: number, enabled: boolean): Promise<MonitoredChat> {
  const { data } = await apiClient.patch<MonitoredChat>(`/whatsapp-monitor/chats/${id}`, {
    enabled,
  });
  return data;
}

export async function removeChat(id: number): Promise<void> {
  await apiClient.delete(`/whatsapp-monitor/chats/${id}`);
}

export async function scanChatNow(id: number, signal?: AbortSignal): Promise<ScanResult> {
  const { data } = await apiClient.post<ScanResult>(
    `/whatsapp-monitor/chats/${id}/scan`,
    undefined,
    { timeout: SCAN_TIMEOUT_MS, signal },
  );
  return data;
}

export async function startWhatsAppLogin(): Promise<WhatsAppLoginStatus> {
  const { data } = await apiClient.post<WhatsAppLoginStatus>(
    "/whatsapp-monitor/login/start",
    undefined,
    { timeout: 40000 },
  );
  return data;
}

export async function getWhatsAppLoginStatus(): Promise<WhatsAppLoginStatus> {
  const { data } = await apiClient.get<WhatsAppLoginStatus>("/whatsapp-monitor/login/status", {
    timeout: 15000,
  });
  return data;
}

// Cache-busted so the browser never serves a stale QR image from its own
// cache — the underlying screenshot changes on disk every time
// start/status is polled (see backend router: QR codes rotate every
// ~20-60s) but the URL path itself never changes.
export function qrImageUrl(): string {
  return `/api/v1/whatsapp-monitor/login/qr-image?t=${Date.now()}`;
}
