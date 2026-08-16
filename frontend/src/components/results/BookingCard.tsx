import { ExternalLink, Hotel, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatDuration } from "@/lib/format";
import type { FlightOption, TripTier } from "@/types/trip";

export function FlightBookingCard({ flight, currency }: { flight: FlightOption; currency: string }) {
  const stops = flight.legs.length - 1;
  const route = `${flight.legs[0].from} → ${flight.legs[flight.legs.length - 1].to}`;

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-500/10 text-brand-600 dark:text-brand-500">
          <Plane className="size-5" />
        </span>
        <div>
          <div className="font-medium">
            {flight.airline} · {route}
          </div>
          <div className="mt-0.5 text-sm text-neutral-500 dark:text-neutral-400">
            {formatDuration(flight.durationMinutes)} · {stops === 0 ? "Nonstop" : `${stops} stop${stops > 1 ? "s" : ""}`} ·{" "}
            {formatCurrency(flight.price, currency)}
          </div>
        </div>
      </div>
      <div className="shrink-0">
        <Button
          variant="outline"
          size="lg"
          className="h-11 w-full rounded-full sm:w-auto"
          nativeButton={false}
          render={<a href={flight.bookingUrl} target="_blank" rel="noopener noreferrer" />}
        >
          Book flight
          <ExternalLink className="size-4" />
        </Button>
        <p className="mt-1.5 text-center text-xs text-neutral-400">Opens Kiwi.com</p>
      </div>
    </div>
  );
}

export function StayBookingCard({ stay, currency }: { stay: TripTier["stay"]; currency: string }) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-accent-500/10 text-accent-600">
          <Hotel className="size-5" />
        </span>
        <div>
          <div className="font-medium">{stay.name}</div>
          <div className="mt-0.5 text-sm text-neutral-500 dark:text-neutral-400">
            {stay.type} · {formatCurrency(stay.pricePerNight, currency)}/night
          </div>
        </div>
      </div>
      <div className="shrink-0">
        <Button
          variant="outline"
          size="lg"
          className="h-11 w-full rounded-full sm:w-auto"
          nativeButton={false}
          render={<a href={stay.bookingUrl} target="_blank" rel="noopener noreferrer" />}
        >
          Book stay
          <ExternalLink className="size-4" />
        </Button>
        <p className="mt-1.5 text-center text-xs text-neutral-400">Opens Booking.com</p>
      </div>
    </div>
  );
}
