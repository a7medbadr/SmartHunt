import { apiClient } from "@/lib/api-client";

export type ActivityType =
  | "resume_uploaded"
  | "application_created"
  | "favorite_added"
  | "saved_search_created"
  | "cover_letter_generated";

export interface Activity {
  id: number;
  type: ActivityType;
  title: string;
  details: string | null;
  created_at: string;
}

export async function getRecentActivities(limit?: number): Promise<Activity[]> {
  const { data } = await apiClient.get<Activity[]>("/activity", {
    params: limit ? { limit } : undefined,
  });
  return data;
}
