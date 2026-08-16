import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ApiError, generateTripResult } from "@/lib/api";
import { useTripStore } from "@/store/tripStore";

const STATUS_LINES = [
  "Searching flights across 40+ airlines…",
  "Found the cheapest combination…",
  "Estimating costs for 3 travel styles…",
  "Writing your day-by-day plans…",
  "Almost there…",
];

const LINE_INTERVAL_MS = 950;

export function GeneratingPage() {
  const navigate = useNavigate();
  const searchInput = useTripStore((state) => state.searchInput);
  const setActiveTripId = useTripStore((state) => state.setActiveTripId);
  const [lineIndex, setLineIndex] = useState(0);
  const hasNavigated = useRef(false);

  useEffect(() => {
    if (!searchInput) {
      navigate("/plan", { replace: true });
      return;
    }

    let cancelled = false;

    const runStatusLines = async () => {
      for (let i = 0; i < STATUS_LINES.length; i += 1) {
        if (cancelled) return;
        setLineIndex(i);
        await new Promise((resolve) => setTimeout(resolve, LINE_INTERVAL_MS));
      }
    };

    const generate = async () => {
      try {
        const [result] = await Promise.all([generateTripResult(searchInput), runStatusLines()]);
        if (cancelled || hasNavigated.current) return;
        hasNavigated.current = true;
        setActiveTripId(result.tripId);
        navigate(`/results/${result.tripId}`, { replace: true });
      } catch (err) {
        if (cancelled || hasNavigated.current) return;
        hasNavigated.current = true;
        const message =
          err instanceof ApiError ? err.message : "We couldn't generate that trip. Check the details and try again.";
        toast.error(message);
        navigate("/plan", { replace: true });
      }
    };

    generate();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-6 py-16">
      <div
        className="animate-gradient-shift absolute inset-0 -z-10 bg-[linear-gradient(135deg,var(--color-brand-50)_0%,var(--background)_40%,var(--color-brand-100)_80%)] bg-[length:220%_220%] opacity-70"
        aria-hidden
      />

      <FlightPath />

      <div className="mt-10 flex w-full max-w-md flex-col items-center text-center">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">Building your trip options</h1>
        <p className="mt-2 text-neutral-500 dark:text-neutral-400">
          Comparing flights, stays, and day plans across three travel styles.
        </p>

        <div className="mt-10 flex w-full flex-col gap-3">
          <AnimatePresence initial={false}>
            {STATUS_LINES.slice(0, lineIndex + 1).map((line, index) => {
              const isCurrent = index === lineIndex;
              return (
                <motion.div
                  key={line}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: isCurrent ? 1 : 0.35, y: 0 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="flex items-center gap-3 text-left"
                >
                  <span
                    className={`flex size-2 shrink-0 rounded-full ${isCurrent ? "animate-pulse bg-brand-500" : "bg-brand-500/40"}`}
                  />
                  <span className={`text-sm sm:text-base ${isCurrent ? "font-medium text-neutral-800 dark:text-neutral-100" : "text-neutral-500 dark:text-neutral-400"}`}>
                    {line}
                  </span>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function FlightPath() {
  return (
    <svg width="220" height="90" viewBox="0 0 220 90" fill="none" className="text-brand-500" aria-hidden>
      <path
        d="M10 70 Q 60 10, 110 40 T 210 20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="6 8"
        className="animate-flight-path opacity-70"
      />
      <circle cx="10" cy="70" r="4" fill="currentColor" />
      <circle cx="210" cy="20" r="4" className="fill-accent-500" />
    </svg>
  );
}
