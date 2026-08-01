import { apiClient } from "@/lib/api-client";

export interface QuickApplyPayload {
  url: string;
  title: string;
  company: string;
  provider?: string;
}

export interface ApplyQueueItem {
  id: number;
  job_id: number;
  provider: string;
  status: string;
  priority: number;
  created_at: string;
  updated_at: string;
}

export async function quickApply(payload: QuickApplyPayload): Promise<ApplyQueueItem> {
  const { data } = await apiClient.post<ApplyQueueItem>("/apply-queue/quick-apply", payload);
  return data;
}
