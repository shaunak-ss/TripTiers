import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageTransition } from "@/components/layout/PageTransition";
import { ComparisonToggle } from "@/components/results/ComparisonToggle";
import { DestinationImage } from "@/components/results/DestinationImage";
import { TierCard } from "@/components/results/TierCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateRange, tripLengthNights } from "@/lib/dates";
import { staggerContainer } from "@/lib/motion";
import { getTripResult } from "@/lib/api";
import type { TripResult } from "@/types/trip";

export function ResultsPage() {
  const { tripId } = useParams<{ tripId: string }>();
  const [trip, setTrip] = useState<TripResult | null | undefined>(undefined);
  const [showDifferences, setShowDifferences] = useState(false);

  useEffect(() => {
    if (!tripId) return;
    let cancelled = false;
    setTrip(undefined);
    getTripResult(tripId).then((result) => {
      if (!cancelled) setTrip(result ?? null);
    });
    return () => {
      cancelled = true;
    };
  }, [tripId]);

  if (trip === null) {
    return (
      <PageTransition>
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
          <h1 className="font-display text-2xl font-semibold">We couldn't find that trip</h1>
          <p className="text-neutral-500 dark:text-neutral-400">It may have expired — let's start a new search.</p>
          <Button
            size="lg"
            className="h-12 rounded-full"
            nativeButton={false}
            render={<Link to="/plan">Plan a new trip</Link>}
          />
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
        {trip ? (
          <div className="relative mb-8 h-40 w-full overflow-hidden rounded-2xl sm:mb-10 sm:h-52">
            <DestinationImage destination={trip.input.destination} priority className="size-full" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/5 to-transparent" />
          </div>
        ) : (
          <Skeleton className="mb-8 h-40 w-full rounded-2xl sm:mb-10 sm:h-52" />
        )}

        <div className="mb-8 flex flex-col gap-4 sm:mb-10 sm:flex-row sm:items-end sm:justify-between">
          <div>
            {trip ? (
              <>
                <p className="text-sm font-medium tracking-wide text-brand-600 uppercase dark:text-brand-500">
                  {trip.input.originCity} → {trip.input.destination}
                </p>
                <h1 className="mt-1 font-display text-2xl font-semibold sm:text-3xl">
                  {formatDateRange(trip.input.startDate, trip.input.endDate)} ·{" "}
                  {tripLengthNights(trip.input.startDate, trip.input.endDate)} nights
                </h1>
                <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                  Three ways to take this trip. Pick the one that feels like you.
                </p>
              </>
            ) : (
              <>
                <Skeleton className="h-4 w-40" />
                <Skeleton className="mt-2 h-8 w-64" />
                <Skeleton className="mt-2 h-4 w-56" />
              </>
            )}
          </div>

          {trip && <ComparisonToggle active={showDifferences} onToggle={() => setShowDifferences((v) => !v)} />}
        </div>

        {trip ? (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="flex gap-5 overflow-x-auto pb-4 [scrollbar-width:none] snap-x snap-mandatory [-ms-overflow-style:none] lg:grid lg:grid-cols-3 lg:overflow-visible lg:snap-none lg:pb-0 [&::-webkit-scrollbar]:hidden"
          >
            {trip.tiers.map((tier) => (
              <TierCard
                key={tier.tier}
                tripId={trip.tripId}
                tier={tier}
                currency={trip.currency}
                isRecommended={tier.tier === "comfort"}
                showDifferences={showDifferences}
              />
            ))}
          </motion.div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex flex-col gap-4 rounded-2xl border border-border p-6">
                <Skeleton className="h-10 w-10 rounded-full" />
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="mt-4 h-12 w-full rounded-full" />
              </div>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
