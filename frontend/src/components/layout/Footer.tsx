import { Compass, PlaneTakeoff, ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-neutral-50 dark:bg-neutral-900/40">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2 font-display text-lg font-semibold">
              <span className="flex size-7 items-center justify-center rounded-full bg-brand-500 text-white">
                <Compass className="size-4" strokeWidth={2.25} />
              </span>
              TripTiers
            </div>
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-neutral-500 dark:text-neutral-400">
              One trip, three ways to take it. Search once, compare real options, book with confidence.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 sm:gap-10">
            <div className="flex items-center gap-2 text-sm font-medium text-neutral-700 dark:text-neutral-300">
              <PlaneTakeoff className="size-4 text-brand-500" />
              Real flight prices
            </div>
            <div className="flex items-center gap-2 text-sm font-medium text-neutral-700 dark:text-neutral-300">
              <ShieldCheck className="size-4 text-brand-500" />
              No hidden fees
            </div>
          </div>
        </div>

        {/* TODO: real testimonials once we have users */}

        <div className="mt-10 border-t border-border/60 pt-6 text-xs text-neutral-400">
          © {new Date().getFullYear()} TripTiers. Built for travelers who hate deciding alone.
        </div>
      </div>
    </footer>
  );
}
