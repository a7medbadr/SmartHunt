import { apiClient } from "@/lib/api-client";

export interface ProviderInfo {
  name: string;
  enabled: boolean;
  supports_login: boolean;
  supports_apply: boolean;
  supports_resume_upload: boolean;
  supports_cover_letter: boolean;
  real_discovery: boolean;
}

export async function listProviders(): Promise<ProviderInfo[]> {
  const { data } = await apiClient.get<ProviderInfo[]>("/providers");
  return data;
}

export async function setProviderEnabled(
  name: string,
  enabled: boolean,
): Promise<ProviderInfo> {
  const { data } = await apiClient.patch<ProviderInfo>(`/providers/${name}`, { enabled });
  return data;
}
