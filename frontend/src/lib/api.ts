import { generateMockTripResult, getMockTripResult } from "@/mocks/api";
import { getAccessToken } from "@/store/authStore";
import type { TripResult, TripSearchInput } from "@/types/trip";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export function isLiveBackendEnabled(): boolean {
  return API_BASE.length > 0;
}

export class ApiError extends Error {
  readonly code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = (await res.json()) as { error?: string; message?: string };
    return new ApiError(body.error ?? "request_failed", body.message ?? res.statusText);
  } catch {
    return new ApiError("request_failed", res.statusText);
  }
}

/**
 * Creates a trip. Uses the live backend when `VITE_API_URL` is set,
 * otherwise the local mock fixtures so the UI still runs without APIs.
 */
export async function generateTripResult(input: TripSearchInput): Promise<TripResult> {
  if (!API_BASE) return generateMockTripResult(input);

  const res = await fetch(`${API_BASE}/api/trips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) throw await parseError(res);
  return (await res.json()) as TripResult;
}

export async function getTripResult(tripId: string): Promise<TripResult | undefined> {
  if (!API_BASE) return getMockTripResult(tripId);

  const res = await fetch(`${API_BASE}/api/trips/${tripId}`);
  if (res.status === 404) return undefined;
  if (res.status === 202) return undefined;
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as TripResult;
}

export async function saveTripOnBackend(tripId: string, accessToken?: string): Promise<boolean> {
  if (!API_BASE) return false;
  const token = accessToken ?? (await getAccessToken());
  if (!token) return false;
  const res = await fetch(`${API_BASE}/api/trips/${tripId}/save`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.ok;
}
