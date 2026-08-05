import { apiClient } from "@/lib/api-client";

export interface DashboardStatistics {
  jobs: number;
  applications: number;
  favorites: number;
  linkedin_posts: number;
  providers: number;
}

export async function getDashboardStatistics(): Promise<DashboardStatistics> {
  const { data } = await apiClient.get<DashboardStatistics>("/dashboard/statistics");
  return data;
}
