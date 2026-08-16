export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatarHue: number;
}

export type CollabMessageKind = "text" | "choice" | "system";

export interface CollabMessageResolution {
  value: string;
  optionLabel: string;
  setByUserId: string | null;
  setByName: string;
  setAt: string;
}

export interface CollabMessageMeta {
  field?: string;
  options?: string[];
  resolved?: CollabMessageResolution;
}

export interface CollabMessage {
  id: string;
  roomId: string;
  userId: string | null; // null for bot messages
  displayName: string;
  body: string;
  createdAt: string;
  isBot?: boolean;
  kind?: CollabMessageKind; // default "text" if absent (older cached rooms)
  meta?: CollabMessageMeta;
}

export type TripBriefField =
  | "destination"
  | "originCity"
  | "startDate"
  | "endDate"
  | "budget"
  | "travelers"
  | "tier"
  | "pace"
  | "dietary";

export interface TripBriefEntry {
  value: string;
  optionLabel: string;
  setByUserId: string | null;
  setByName: string;
  setAt: string;
}

export type TripBrief = Partial<Record<TripBriefField, TripBriefEntry>>;

export const TRIP_BRIEF_LABELS: Record<TripBriefField, string> = {
  destination: "Destination",
  originCity: "Flying from",
  startDate: "Start date",
  endDate: "End date",
  budget: "Budget",
  travelers: "Travelers",
  tier: "Trip style",
  pace: "Pace",
  dietary: "Dietary needs",
};

export const TRIP_BRIEF_FIELD_ORDER: TripBriefField[] = [
  "destination",
  "originCity",
  "startDate",
  "endDate",
  "travelers",
  "budget",
  "tier",
  "pace",
  "dietary",
];

export interface CollabMember {
  userId: string;
  displayName: string;
  email?: string;
  joinedAt: string;
}

export interface CollabRoom {
  id: string;
  code: string;
  name: string;
  tripId?: string;
  generatedTripId?: string;
  hostUserId: string;
  members: CollabMember[];
  messages: CollabMessage[];
  createdAt: string;
  tripBrief: TripBrief;
}
