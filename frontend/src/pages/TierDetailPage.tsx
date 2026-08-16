import { ArrowLeft, ExternalLink } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageTransition } from "@/components/layout/PageTransition";
import { FlightBookingCard, StayBookingCard } from "@/components/results/BookingCard";
import { DestinationImage } from "@/components/results/DestinationImage";
import { ItineraryDayCard } from "@/components/results/ItineraryDayCard";
import { SaveTripButton } from "@/components/results/SaveTripButton";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/format";
import { TIER_META } from "@/lib/tiers";
import { cn } from "@/lib/utils";
import { getTripResult } from "@/lib/api";
import type { TierId, TripResult } from "@/types/trip";

export function TierDetailPage() {
  const { tripId, tier: tierParam } = useParams<{ tripId: string; tier: TierId }>();
  const [trip, setTrip] = useState<TripResult | null | undefined>(undefined);
  const [openDay, setOpenDay] = useState<number | null>(1);
  const bookingRef = useRef<HTMLDivElement>(null);

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

  if (trip === undefined) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="mt-4 h-24 w-full rounded-2xl" />
          <Skeleton className="mt-4 h-24 w-full rounded-2xl" />
          <Skeleton className="mt-6 h-40 w-full rounded-2xl" />
        </div>
      </PageTransition>
    );
  }

  const tierData = trip?.tiers.find((t) => t.tier === tierParam);

  if (!trip || !tierData) {
    return (
      <PageTransition>
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
          <h1 className="font-display text-2xl font-semibold">We couldn't find that plan</h1>
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

  const meta = TIER_META[tierData.tier];
  const Icon = meta.icon;

  return (
    <PageTransition>
      <div className="pb-40 sm:pb-16">
        <div className="sticky top-16 z-30 border-b border-border/60 bg-white/85 backdrop-blur-md dark:bg-neutral-900/85">
          <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
            <Link
              to={`/results/${trip.tripId}`}
              className="flex size-11 shrink-0 items-center justify-center rounded-full text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label="Back to comparison"
            >
              <ArrowLeft className="size-5" />
            </Link>
            <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-full", meta.bg)}>
              <Icon className={cn("size-4", meta.text)} />
            </span>
            <span className="min-w-0 flex-1 truncate font-display font-semibold">{meta.label} trip</span>
            <span className="shrink-0 font-display text-lg font-semibold">{formatCurrency(tierData.totalPrice, trip.currency)}</span>
          </div>
        </div>

        <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6">
          <div className="relative h-44 w-full overflow-hidden rounded-2xl sm:h-56">
            <DestinationImage
              destination={trip.input.destination}
              priority
              className="size-full"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent" />
            <div className="absolute inset-x-0 bottom-0 p-4 sm:p-5">
              <p className="text-xs font-medium tracking-wide text-white/80 uppercase">
                {trip.input.originCity} → {trip.input.destination}
              </p>
              <h1 className="mt-0.5 font-display text-xl font-semibold text-white sm:text-2xl">
                Your {meta.label.toLowerCase()} plan
              </h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-neutral-500 dark:text-neutral-400">{meta.tagline}</p>

          <div ref={bookingRef} className="mt-6 flex flex-col gap-4">
            <FlightBookingCard flight={tierData.flight} currency={trip.currency} />
            <StayBookingCard stay={tierData.stay} currency={trip.currency} />
          </div>

          <div className="mt-4 hidden flex-col gap-3 sm:flex">
            <Button
              size="lg"
              className="h-12 w-full rounded-full"
              onClick={() => bookingRef.current?.scrollIntoView({ behavior: "smooth" })}
            >
              Book this trip
              <ExternalLink className="size-4" />
            </Button>
            <SaveTripButton
              className="w-full"
              trip={{
                tripId: trip.tripId,
                tier: tierData.tier,
                destination: trip.input.destination,
                startDate: trip.input.startDate,
                endDate: trip.input.endDate,
                savedAt: new Date().toISOString(),
              }}
            />
          </div>

          <h2 className="mt-10 font-display text-xl font-semibold">Day by day</h2>
          <div className="mt-4 flex flex-col gap-3">
            {tierData.itinerary.map((day) => (
              <ItineraryDayCard
                key={day.day}
                day={day}
                isOpen={openDay === day.day}
                onToggle={() => setOpenDay((current) => (current === day.day ? null : day.day))}
                accentDot={meta.dot}
                destination={trip.input.destination}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 flex flex-col gap-2 border-t border-border/60 bg-white/85 px-4 py-3 backdrop-blur-md safe-bottom sm:hidden dark:bg-neutral-900/85">
        <Button
          size="lg"
          className="h-12 w-full rounded-full"
          onClick={() => bookingRef.current?.scrollIntoView({ behavior: "smooth" })}
        >
          Book this trip
        </Button>
        <SaveTripButton
          className="w-full"
          trip={{
            tripId: trip.tripId,
            tier: tierData.tier,
            destination: trip.input.destination,
            startDate: trip.input.startDate,
            endDate: trip.input.endDate,
            savedAt: new Date().toISOString(),
          }}
        />
      </div>
    </PageTransition>
  );
}
