import { tripFixtures } from "@/mocks/fixtures";
import type { TripResult, TripSearchInput, TripTier } from "@/types/trip";

const STORAGE_KEY = "triptiers.generated-trips";

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function readGeneratedTrips(): Record<string, TripResult> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, TripResult>) : {};
  } catch {
    return {};
  }
}

function writeGeneratedTrip(trip: TripResult) {
  if (typeof window === "undefined") return;
  const all = readGeneratedTrips();
  all[trip.tripId] = trip;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
}

function scaleTier(tier: TripTier, budgetRatio: number, travelers: number): TripTier {
  const perTravelerRatio = Math.max(0.55, Math.min(1.8, budgetRatio));
  const flightPrice = Math.round(tier.flight.price * perTravelerRatio);
  const pricePerNight = Math.round(tier.stay.pricePerNight * perTravelerRatio);
  const nights = tier.itinerary.length - 1;
  const totalPrice = Math.round((flightPrice + pricePerNight * nights) * travelers * 0.92);

  return {
    ...tier,
    totalPrice,
    flight: { ...tier.flight, price: flightPrice },
    stay: { ...tier.stay, pricePerNight },
  };
}

/**
 * Simulates a real agent pipeline generating a fresh trip for the given
 * search input. Picks the closest-matching fixture template as a base
 * (in a real backend this would be the actual flight/itinerary search),
 * re-prices it against the requested budget/travelers, and stores the
 * result so it can be re-fetched by id later (including after a reload).
 */
export async function generateMockTripResult(input: TripSearchInput): Promise<TripResult> {
  await wait(900 + Math.random() * 400);

  const destination = input.destination.toLowerCase();
  const template =
    tripFixtures.find((fixture) => fixture.input.destination.toLowerCase().includes(destination) || destination.includes(fixture.input.destination.split(",")[0].toLowerCase())) ??
    tripFixtures[Math.floor(Math.random() * tripFixtures.length)];

  const comfortTier = template.tiers.find((t) => t.tier === "comfort")!;
  const budgetRatio = input.budget > 0 ? input.budget / comfortTier.totalPrice : 1;

  const tripId = `trip-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;

  const result: TripResult = {
    tripId,
    input,
    generatedAt: new Date().toISOString(),
    currency: template.currency,
    tiers: template.tiers.map((tier) => scaleTier(tier, budgetRatio, Math.max(1, input.travelers))),
  };

  writeGeneratedTrip(result);
  return result;
}

/**
 * Fetches a trip result by id. Checks generated (localStorage-backed)
 * trips first, then falls back to the bundled fixtures — shaped like a
 * real async API call so swapping in a live fetch later is a one-line change.
 */
export async function getMockTripResult(tripId: string): Promise<TripResult | undefined> {
  await wait(250);
  const generated = readGeneratedTrips();
  if (generated[tripId]) return generated[tripId];
  return tripFixtures.find((trip) => trip.tripId === tripId);
}

export async function listMockTripResults(): Promise<TripResult[]> {
  await wait(150);
  const generated = Object.values(readGeneratedTrips());
  return [...generated, ...tripFixtures];
}
