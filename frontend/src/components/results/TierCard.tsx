import { motion } from "framer-motion";
import { ArrowRight, Clock, Plane } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatDuration } from "@/lib/format";
import { staggerItem } from "@/lib/motion";
import { TIER_META } from "@/lib/tiers";
import { cn } from "@/lib/utils";
import type { TripTier } from "@/types/trip";

interface TierCardProps {
  tripId: string;
  tier: TripTier;
  currency: string;
  isRecommended?: boolean;
  showDifferences?: boolean;
}

export function TierCard({ tripId, tier, currency, isRecommended, showDifferences }: TierCardProps) {
  const meta = TIER_META[tier.tier];
  const Icon = meta.icon;
  const stops = tier.flight.legs.length - 1;

  return (
    <motion.div
      variants={staggerItem}
      whileHover={{ y: -2 }}
      className={cn(
        "group flex w-[85%] shrink-0 snap-center flex-col overflow-hidden rounded-2xl border bg-card shadow-lg shadow-black/5 transition-shadow sm:w-[48%] lg:w-auto",
        meta.border,
        isRecommended && "lg:scale-105 lg:shadow-xl lg:shadow-brand-500/10"
      )}
    >
      {isRecommended && (
        <div className="bg-brand-500 px-4 py-1.5 text-center text-xs font-semibold tracking-wide text-white uppercase">
          Most travelers pick this
        </div>
      )}

      <div className={cn("flex flex-1 flex-col gap-5 p-6", meta.bg)}>
        <div className="flex items-center gap-3">
          <span className={cn("flex size-10 items-center justify-center rounded-full bg-white shadow-sm dark:bg-neutral-900")}>
            <Icon className={cn("size-5", meta.text)} strokeWidth={2.25} />
          </span>
          <div>
            <div className="font-display text-lg font-semibold">{meta.label}</div>
            <div className="text-xs text-neutral-500 dark:text-neutral-400">{meta.tagline}</div>
          </div>
        </div>

        <div>
          <div className="font-display text-3xl font-semibold sm:text-4xl">{formatCurrency(tier.totalPrice, currency)}</div>
          <div className="text-xs text-neutral-500 dark:text-neutral-400">total trip cost</div>
        </div>

        <ul className="flex flex-col gap-2 text-sm text-neutral-700 dark:text-neutral-300">
          {tier.highlights.slice(0, 4).map((point) => (
            <li key={point} className="flex gap-2">
              <span className={cn("mt-1.5 size-1.5 shrink-0 rounded-full", meta.dot)} />
              {point}
            </li>
          ))}
        </ul>

        {showDifferences && (
          <div className="flex flex-col gap-2 rounded-xl border border-dashed border-neutral-300 bg-white/70 p-3 text-xs text-neutral-600 dark:border-neutral-700 dark:bg-neutral-900/50 dark:text-neutral-300">
            <div className="flex items-center gap-1.5">
              <Plane className="size-3.5" />
              {tier.flight.airline} · {stops === 0 ? "Nonstop" : `${stops} stop${stops > 1 ? "s" : ""}`}
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="size-3.5" />
              {formatDuration(tier.flight.durationMinutes)} · {tier.stay.type}
            </div>
          </div>
        )}

        <div className="mt-auto flex flex-col gap-2 pt-2">
          <Button
            size="lg"
            className="h-12 w-full rounded-full"
            nativeButton={false}
            render={<Link to={`/results/${tripId}/${tier.tier}`} />}
          >
            Select this trip
            <ArrowRight className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="lg"
            className="h-11 w-full rounded-full"
            nativeButton={false}
            render={<Link to={`/results/${tripId}/${tier.tier}`} />}
          >
            See full plan
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
