import { apiClient } from "@/lib/api-client";

export interface HealthDetails {
  status: string;
  database: string;
  scheduler: string;
  playwright: string;
  version: string;
}

export async function getHealthDetails(): Promise<HealthDetails> {
  const { data } = await apiClient.get<HealthDetails>("/health/details");
  return data;
}

export interface SystemVersion {
  application: string;
  version: string;
  environment: string;
  python: string;
  build: string;
}

export async function getSystemVersion(): Promise<SystemVersion> {
  const { data } = await apiClient.get<SystemVersion>("/system/version");
  return data;
}

export interface AIProviderHealth {
  provider: string;
  available: boolean;
  message: string | null;
}

export interface AIHealth {
  status: string;
  providers: AIProviderHealth[];
}

export async function getAIHealth(): Promise<AIHealth> {
  const { data } = await apiClient.get<AIHealth>("/ai/health");
  return data;
}

export interface ProviderHealthDetail {
  id: number;
  provider: string;
  status: string;
  last_check: string;
  response_time_ms: number | null;
  message: string | null;
}

export async function listProviderHealth(): Promise<ProviderHealthDetail[]> {
  const { data } = await apiClient.get<ProviderHealthDetail[]>("/providers/health");
  return data;
}
