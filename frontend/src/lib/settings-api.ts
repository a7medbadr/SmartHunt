import { apiClient } from "@/lib/api-client";

export interface UserSettings {
  theme: string;
  language: string;
  email_notifications: boolean;
  job_alerts: boolean;
}

export async function getSettings(): Promise<UserSettings> {
  const { data } = await apiClient.get<UserSettings>("/settings");
  return data;
}

export async function updateSettings(payload: UserSettings): Promise<UserSettings> {
  const { data } = await apiClient.put<UserSettings>("/settings", payload);
  return data;
}
