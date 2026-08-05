import { apiClient } from "@/lib/api-client";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function register(payload: RegisterPayload): Promise<CurrentUser> {
  const { data } = await apiClient.post<CurrentUser>("/auth/register", payload);
  return data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const { data } = await apiClient.get<CurrentUser>("/auth/me");
  return data;
}

export async function refreshToken(): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/refresh");
  return data;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await apiClient.post("/auth/change-password", payload);
}
