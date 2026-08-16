import { isLiveBackendEnabled } from "@/lib/api";
import { authHeaders } from "@/lib/authHeaders";
import type { CollabMessage, CollabRoom } from "@/types/collab";
import type { SavedTrip } from "@/store/tripStore";
import type { TripResult } from "@/types/trip";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

async function parseJson(res: Response) {
  return (await res.json()) as Record<string, unknown>;
}

export async function fetchMyRooms(): Promise<CollabRoom[]> {
  if (!isLiveBackendEnabled()) return [];
  const res = await fetch(`${API_BASE}/api/me/rooms`, { headers: await authHeaders(false) });
  if (!res.ok) return [];
  return (await res.json()) as CollabRoom[];
}

export async function fetchMySavedTrips(): Promise<SavedTrip[]> {
  if (!isLiveBackendEnabled()) return [];
  const res = await fetch(`${API_BASE}/api/me/trips`, { headers: await authHeaders(false) });
  if (!res.ok) return [];
  return (await res.json()) as SavedTrip[];
}

export async function syncCreateRoom(input: { name: string; tripId?: string }): Promise<CollabRoom> {
  const res = await fetch(`${API_BASE}/api/collab/rooms`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ name: input.name, tripId: input.tripId }),
  });
  if (!res.ok) {
    const body = await parseJson(res);
    throw new Error((body.message as string) || "Could not create room.");
  }
  return (await res.json()) as CollabRoom;
}

export async function syncJoinRoom(input: { code: string }): Promise<CollabRoom> {
  const res = await fetch(`${API_BASE}/api/collab/rooms/join`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ code: input.code }),
  });
  if (!res.ok) {
    const body = await parseJson(res);
    throw new Error((body.message as string) || "Could not join room.");
  }
  return (await res.json()) as CollabRoom;
}

export async function fetchRoom(code: string): Promise<CollabRoom | null> {
  if (!isLiveBackendEnabled()) return null;
  const res = await fetch(`${API_BASE}/api/collab/rooms/${encodeURIComponent(code)}`, {
    headers: await authHeaders(false),
  });
  if (!res.ok) return null;
  return (await res.json()) as CollabRoom;
}

export async function syncPostMessage(input: { code: string; body: string }): Promise<CollabMessage> {
  const res = await fetch(`${API_BASE}/api/collab/rooms/${encodeURIComponent(input.code)}/messages`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ body: input.body }),
  });
  if (!res.ok) {
    const parsed = await parseJson(res);
    throw new Error((parsed.message as string) || "Could not send.");
  }
  return (await res.json()) as CollabMessage;
}

export async function syncSelectOption(input: {
  code: string;
  messageId: string;
  value: string;
}): Promise<CollabMessage> {
  const res = await fetch(
    `${API_BASE}/api/collab/rooms/${encodeURIComponent(input.code)}/messages/${encodeURIComponent(input.messageId)}/select`,
    {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({ value: input.value }),
    }
  );
  if (!res.ok) {
    const parsed = await parseJson(res);
    throw new Error((parsed.message as string) || "Could not select that.");
  }
  return (await res.json()) as CollabMessage;
}

export interface GenerateFromChatInput {
  roomCode: string;
  memberCount: number;
  messages: Array<{ displayName: string; body: string; createdAt?: string }>;
}

export interface GenerateFromChatResponse {
  trip?: TripResult;
  missingFields?: string[];
  notes?: string;
  message?: string;
}

export async function generateItineraryFromChat(
  input: GenerateFromChatInput
): Promise<GenerateFromChatResponse> {
  if (!isLiveBackendEnabled()) {
    return {
      missingFields: ["live backend"],
      message: "Set VITE_API_URL so the group discussion can be turned into a real itinerary.",
    };
  }

  const res = await fetch(`${API_BASE}/api/collab/generate`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(input),
  });
  const body = (await parseJson(res)) as GenerateFromChatResponse & { details?: string[] };
  if (!res.ok) {
    return {
      missingFields: body.details ?? body.missingFields,
      notes: body.notes,
      message: body.message ?? "Could not generate an itinerary from this chat yet.",
    };
  }
  return body;
}

export function serializeMessages(messages: CollabMessage[]) {
  return messages.map((message) => ({
    displayName: message.displayName,
    body: message.body,
    createdAt: message.createdAt,
  }));
}
