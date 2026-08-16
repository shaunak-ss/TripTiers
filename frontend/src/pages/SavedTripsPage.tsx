import { motion } from "framer-motion";
import { ArrowRight, Luggage, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { PageTransition } from "@/components/layout/PageTransition";
import { DestinationImage } from "@/components/results/DestinationImage";
import { Button } from "@/components/ui/button";
import { formatDateRange } from "@/lib/dates";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { TIER_META } from "@/lib/tiers";
import { cn } from "@/lib/utils";
import { useTripStore } from "@/store/tripStore";

export function SavedTripsPage() {
  const savedTrips = useTripStore((state) => state.savedTrips);

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">My trips</h1>
        <p className="mt-1 text-neutral-500 dark:text-neutral-400">Every trip you've saved, ready to pick back up.</p>

        {savedTrips.length === 0 ? (
          <div className="mt-10 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border py-16 text-center">
            <span className="flex size-14 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-900/40">
              <Luggage className="size-7" />
            </span>
            <h2 className="font-display text-xl font-semibold">No saved trips yet</h2>
            <p className="max-w-sm text-sm text-neutral-500 dark:text-neutral-400">
              Once you find a trip you love, save it here so it's easy to come back to — no re-searching required.
            </p>
            <Button
              size="lg"
              className="mt-2 h-12 rounded-full px-6"
              nativeButton={false}
              render={<Link to="/plan">Plan my trip</Link>}
            />
          </div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
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
                      <span
                        className={cn(
                          "absolute top-3 left-3 flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold shadow-sm backdrop-blur-sm dark:bg-neutral-900/85"
                        )}
                      >
                        <Icon className={cn("size-3.5", meta.text)} />
                        {meta.label}
                      </span>
                    </div>
                    <div className={cn("flex flex-1 flex-col gap-3 p-5", meta.bg)}>
                      <div className="flex items-center gap-1.5 text-sm font-medium text-neutral-700 dark:text-neutral-200">
                        <MapPin className="size-3.5 shrink-0" />
                        <span className="truncate">{trip.destination}</span>
                      </div>
                      <div className="text-xs text-neutral-500 dark:text-neutral-400">
                        {formatDateRange(trip.startDate, trip.endDate)}
                      </div>
                      <span className="mt-auto flex items-center gap-1 pt-2 text-sm font-medium text-brand-600 dark:text-brand-500">
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
      </div>
    </PageTransition>
  );
}
