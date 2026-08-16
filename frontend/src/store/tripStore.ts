import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { TierId, TripSearchInput } from "@/types/trip";

export interface SavedTrip {
  tripId: string;
  tier: TierId;
  destination: string;
  startDate: string;
  endDate: string;
  savedAt: string;
}

interface TripStoreState {
  searchInput: TripSearchInput | null;
  activeTripId: string | null;
  savedTrips: SavedTrip[];
  setSearchInput: (input: TripSearchInput) => void;
  setActiveTripId: (tripId: string) => void;
  saveTrip: (trip: SavedTrip) => void;
  unsaveTrip: (tripId: string, tier: TierId) => void;
  isTripSaved: (tripId: string, tier: TierId) => boolean;
}

export const useTripStore = create<TripStoreState>()(
  persist(
    (set, get) => ({
      searchInput: null,
      activeTripId: null,
      savedTrips: [],
      setSearchInput: (input) => set({ searchInput: input }),
      setActiveTripId: (tripId) => set({ activeTripId: tripId }),
      saveTrip: (trip) =>
        set((state) => {
          if (state.savedTrips.some((t) => t.tripId === trip.tripId && t.tier === trip.tier)) {
            return state;
          }
          return { savedTrips: [trip, ...state.savedTrips] };
        }),
      unsaveTrip: (tripId, tier) =>
        set((state) => ({
          savedTrips: state.savedTrips.filter((t) => !(t.tripId === tripId && t.tier === tier)),
        })),
      isTripSaved: (tripId, tier) => get().savedTrips.some((t) => t.tripId === tripId && t.tier === tier),
    }),
    {
      name: "triptiers.trip-store",
      partialize: (state) => ({ savedTrips: state.savedTrips, searchInput: state.searchInput }),
    }
  )
);
