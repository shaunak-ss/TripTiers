import { getAccessToken } from "@/store/authStore";

export async function authHeaders(json = true): Promise<HeadersInit> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}
