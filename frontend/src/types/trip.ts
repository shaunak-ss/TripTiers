export type TierId = "backpacker" | "comfort" | "luxury";

export interface TripSearchInput {
  destination: string;
  originCity: string;
  startDate: string; // ISO date
  endDate: string; // ISO date
  budget: number; // in user's local currency, numeric
  travelers: number;
}

export interface FlightOption {
  airline: string;
  legs: { from: string; to: string; carrier: string }[]; // >1 leg = interlined combo
  price: number;
  durationMinutes: number;
  bookingUrl: string; // external deep-link (mocked for now)
}

export interface ItineraryDay {
  day: number;
  title: string;
  morning: string;
  afternoon: string;
  evening: string;
}

export interface TripTier {
  tier: TierId;
  totalPrice: number;
  flight: FlightOption;
  stay: { name: string; type: string; pricePerNight: number; bookingUrl: string };
  highlights: string[]; // 3-4 short bullets shown on the comparison card
  itinerary: ItineraryDay[];
}

export interface TripResult {
  tripId: string;
  input: TripSearchInput;
  tiers: TripTier[]; // always exactly 3, order: backpacker, comfort, luxury
  generatedAt: string;
  currency: string; // ISO 4217 code for flight/stay/totalPrice fields — destination-local, not the search budget's currency
  groupPreferencesSummary?: string; // only present for collab-generated trips
}

