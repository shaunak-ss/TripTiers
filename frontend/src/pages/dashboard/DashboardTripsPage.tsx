import { motion } from "framer-motion";
import { ArrowRight, Luggage, MapPin, MessagesSquare } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import { PageTransition } from "@/components/layout/PageTransition";
import { DestinationImage } from "@/components/results/DestinationImage";
import { Button } from "@/components/ui/button";
import { fetchMyRooms, fetchMySavedTrips } from "@/lib/collabApi";
import { formatDateRange } from "@/lib/dates";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { TIER_META } from "@/lib/tiers";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useCollabStore } from "@/store/collabStore";
import type { SavedTrip } from "@/store/tripStore";

const PAGE_SIZE = 20;

export function DashboardTripsPage() {
  const user = useAuthStore((state) => state.user);
  const rooms = useCollabStore(useShallow((state) => (user ? state.roomsForUser(user.id) : [])));
  const setRooms = useCollabStore((state) => state.setRooms);
  const [roomsPage, setRoomsPage] = useState(1);
  const [roomsHasMore, setRoomsHasMore] = useState(false);
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([]);
  const [tripsPage, setTripsPage] = useState(1);
  const [tripsHasMore, setTripsHasMore] = useState(false);

  useEffect(() => {
    void fetchMyRooms(1, PAGE_SIZE).then((result) => {
      setRooms(result.items);
      setRoomsPage(1);
      setRoomsHasMore(result.hasMore);
    });
    void fetchMySavedTrips(1, PAGE_SIZE).then((result) => {
      setSavedTrips(result.items);
      setTripsPage(1);
      setTripsHasMore(result.hasMore);
    });
  }, [setRooms]);

  const loadMoreRooms = async () => {
    const nextPage = roomsPage + 1;
    const result = await fetchMyRooms(nextPage, PAGE_SIZE);
    setRooms([...rooms, ...result.items]);
    setRoomsPage(nextPage);
    setRoomsHasMore(result.hasMore);
  };

  const loadMoreTrips = async () => {
    const nextPage = tripsPage + 1;
    const result = await fetchMySavedTrips(nextPage, PAGE_SIZE);
    setSavedTrips((prev) => [...prev, ...result.items]);
    setTripsPage(nextPage);
    setTripsHasMore(result.hasMore);
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-12">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">My trips</h1>
        <p className="mt-1 text-neutral-500 dark:text-neutral-400">
          Saved plans and rooms you're planning with friends.
        </p>

        {rooms.length > 0 && (
          <section className="mt-8">
            <h2 className="font-display text-lg font-semibold">Planning rooms</h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {rooms.map((room) => (
                <Link
                  key={room.id}
                  to={`/dashboard/rooms/${room.code}`}
                  className="flex items-start gap-3 rounded-2xl border border-border p-4 transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                    <MessagesSquare className="size-4.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{room.name}</p>
                    <p className="text-xs text-neutral-500">
                      Code {room.code} · {room.members.length} {room.members.length === 1 ? "member" : "members"}
                    </p>
                  </div>
                  <ArrowRight className="mt-1 size-4 shrink-0 text-neutral-400" />
                </Link>
              ))}
            </div>
            {roomsHasMore && (
              <div className="mt-4 flex justify-center">
                <Button variant="outline" size="sm" onClick={() => void loadMoreRooms()}>
                  Load more rooms
                </Button>
              </div>
            )}
          </section>
        )}

        <section className="mt-10">
          <h2 className="font-display text-lg font-semibold">Saved trips</h2>
          {savedTrips.length === 0 ? (
            <div className="mt-4 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border py-14 text-center">
              <span className="flex size-14 items-center justify-center rounded-full bg-brand-50 text-brand-500">
                <Luggage className="size-7" />
              </span>
              <h3 className="font-display text-xl font-semibold">No saved trips yet</h3>
              <p className="max-w-sm text-sm text-neutral-500">
                Generate a trip, then tap “Log in to save and share trip with friends” to keep it here.
              </p>
              <Button
                size="lg"
                className="h-12 rounded-full px-6"
                nativeButton={false}
                render={<Link to="/plan">Plan my trip</Link>}
              />
            </div>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
              className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            >
              {savedTrips.map((trip) => {
                const meta = TIER_META[trip.tier];
                const Icon = meta.icon;
                return (
                  <motion.div key={`${trip.tripId}-${trip.tier}`} variants={staggerItem}>
                    <Link
                      to={`/results/${trip.tripId}/${trip.tier}`}
                      className={cn(
                        "flex h-full flex-col overflow-hidden rounded-2xl border shadow-lg shadow-black/5 transition-transform hover:-translate-y-0.5",
                        meta.border
                      )}
                    >
                      <div className="relative h-28 w-full">
                        <DestinationImage destination={trip.destination} width={480} className="size-full" />
                        <span className="absolute top-3 left-3 flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold shadow-sm backdrop-blur-sm">
                          <Icon className={cn("size-3.5", meta.text)} />
                          {meta.label}
                        </span>
                      </div>
                      <div className={cn("flex flex-1 flex-col gap-3 p-5", meta.bg)}>
                        <div className="flex items-center gap-1.5 text-sm font-medium">
                          <MapPin className="size-3.5 shrink-0" />
                          <span className="truncate">{trip.destination}</span>
                        </div>
                        <div className="text-xs text-neutral-500">{formatDateRange(trip.startDate, trip.endDate)}</div>
                        <span className="mt-auto flex items-center gap-1 pt-2 text-sm font-medium text-brand-600">
                          View trip
                          <ArrowRight className="size-3.5" />
                        </span>
                      </div>
                    </Link>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
          {tripsHasMore && (
            <div className="mt-4 flex justify-center">
              <Button variant="outline" size="sm" onClick={() => void loadMoreTrips()}>
                Load more trips
              </Button>
            </div>
          )}
        </section>
      </div>
    </PageTransition>
  );
}
