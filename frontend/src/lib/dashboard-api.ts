import { apiClient } from "@/lib/api-client";

export interface DashboardStatistics {
  jobs: number;
  applications: number;
  favorites: number;
  linkedin_posts: number;
  whatsapp_posts: number;
  job_sites: number;
  not_suitable_jobs: number;
  providers: number;
}

export async function getDashboardStatistics(): Promise<DashboardStatistics> {
  const { data } = await apiClient.get<DashboardStatistics>("/dashboard/statistics");
  return data;
}

export interface DashboardTimeseriesPoint {
  date: string;
  job_sites: number;
  linkedin_posts: number;
  whatsapp_posts: number;
  applications: number;
}

export interface DashboardTimeseries {
  points: DashboardTimeseriesPoint[];
}

export async function getDashboardTimeseries(days: number): Promise<DashboardTimeseries> {
  const { data } = await apiClient.get<DashboardTimeseries>("/dashboard/timeseries", {
    params: { days },
  });
  return data;
}
