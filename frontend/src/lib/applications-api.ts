import { apiClient } from "@/lib/api-client";

export const APPLICATION_STATUSES = [
  "Applied",
  "Interviewing",
  "Technical Interview",
  "Offered",
  "Rejected",
  "Pending",
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export interface Application {
  id: string;
  job_title: string;
  company: string;
  url: string | null;
  status: ApplicationStatus;
  created_at: string;
  days_since_applied: number;
  needs_follow_up: boolean;
}

export interface ApplicationCreatePayload {
  job_title: string;
  company: string;
  url?: string;
  status?: ApplicationStatus;
}

export async function listApplications(): Promise<Application[]> {
  const { data } = await apiClient.get<Application[]>("/applications");
  return data;
}

export async function createApplication(
  payload: ApplicationCreatePayload,
): Promise<Application> {
  const { data } = await apiClient.post<Application>("/applications", payload);
  return data;
}

export async function updateApplicationStatus(
  id: string,
  status: ApplicationStatus,
): Promise<Application> {
  const { data } = await apiClient.patch<Application>(`/applications/${id}`, {
    status,
  });
  return data;
}

export async function deleteApplication(id: string): Promise<void> {
  await apiClient.delete(`/applications/${id}`);
}
