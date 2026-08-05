import { apiClient } from "@/lib/api-client";

// Same CPU-bound local model as the other AI drafting features — see
// ai-mutation-key.ts's comment for the live-measured queueing numbers
// behind why this needs real margin, not just over a single attempt.
const EMAIL_APPLY_TIMEOUT_MS = 650000;

export interface DraftEmailResult {
  recipient_email: string;
  subject: string;
  body: string;
}

export async function draftApplicationEmail(jobId: number): Promise<DraftEmailResult> {
  const { data } = await apiClient.post<DraftEmailResult>(
    "/email-apply/draft",
    { job_id: jobId },
    { timeout: EMAIL_APPLY_TIMEOUT_MS },
  );
  return data;
}

export interface EmailMessage {
  id: string;
  application_id: string;
  direction: "outbound" | "inbound";
  from_address: string;
  to_address: string;
  subject: string;
  body: string;
  created_at: string;
}

export async function sendApplicationEmail(payload: {
  jobId: number;
  recipientEmail: string;
  subject: string;
  body: string;
}): Promise<EmailMessage> {
  const { data } = await apiClient.post<EmailMessage>("/email-apply/send", {
    job_id: payload.jobId,
    recipient_email: payload.recipientEmail,
    subject: payload.subject,
    body: payload.body,
  });
  return data;
}

export async function getEmailThread(applicationId: string): Promise<EmailMessage[]> {
  const { data } = await apiClient.get<EmailMessage[]>(`/email-apply/${applicationId}/thread`);
  return data;
}

export async function draftReply(applicationId: string): Promise<{ body: string }> {
  const { data } = await apiClient.post<{ body: string }>(
    `/email-apply/${applicationId}/reply/draft`,
    undefined,
    { timeout: EMAIL_APPLY_TIMEOUT_MS },
  );
  return data;
}

export async function sendReply(applicationId: string, body: string): Promise<EmailMessage> {
  const { data } = await apiClient.post<EmailMessage>(`/email-apply/${applicationId}/reply/send`, {
    body,
  });
  return data;
}
