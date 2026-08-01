import { apiClient } from "@/lib/api-client";

export interface SavedSearch {
  id: number;
  name: string;
  keyword: string | null;
  location: string | null;
  created_at: string;
}

export interface SavedSearchCreatePayload {
  name: string;
  keyword?: string;
  location?: string;
}

export async function listSavedSearches(): Promise<SavedSearch[]> {
  const { data } = await apiClient.get<SavedSearch[]>("/saved-searches");
  return data;
}

export async function createSavedSearch(
  payload: SavedSearchCreatePayload,
): Promise<SavedSearch> {
  const { data } = await apiClient.post<SavedSearch>("/saved-searches", payload);
  return data;
}

export async function deleteSavedSearch(id: number): Promise<void> {
  await apiClient.delete(`/saved-searches/${id}`);
}
