import { apiClient } from "@/lib/api-client";

export interface Notification {
  id: number;
  user_id: number | null;
  type: string;
  title: string;
  message: string;
  status: string;
  channel: string;
  priority: string;
  created_at: string;
  read_at: string | null;
  expires_at: string | null;
}

export async function listNotifications(): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>("/notifications");
  return data;
}

export interface NotificationCreatePayload {
  type?: string;
  title: string;
  message: string;
  channel?: string;
  priority?: string;
}

export async function createNotification(
  payload: NotificationCreatePayload,
): Promise<Notification> {
  const { data } = await apiClient.post<Notification>("/notifications", payload);
  return data;
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await apiClient.get<{ count: number }>(
    "/notifications/unread-count",
  );
  return data.count;
}

export async function markNotificationRead(id: number): Promise<void> {
  await apiClient.post(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post("/notifications/read-all");
}

export async function deleteNotification(id: number): Promise<void> {
  await apiClient.delete(`/notifications/${id}`);
}
