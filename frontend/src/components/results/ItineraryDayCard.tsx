import { motion } from "framer-motion";
import { ChevronDown, Moon, Sun, Sunrise } from "lucide-react";
import { DestinationImage } from "@/components/results/DestinationImage";
import { cn } from "@/lib/utils";
import type { ItineraryDay } from "@/types/trip";

const BLOCKS = [
  { key: "morning" as const, label: "Morning", icon: Sunrise },
  { key: "afternoon" as const, label: "Afternoon", icon: Sun },
  { key: "evening" as const, label: "Evening", icon: Moon },
];

export function ItineraryDayCard({
  day,
  isOpen,
  onToggle,
  accentDot,
  destination,
}: {
  day: ItineraryDay;
  isOpen: boolean;
  onToggle: () => void;
  accentDot: string;
  destination: string;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        className="flex min-h-16 w-full items-center gap-4 px-5 py-4 text-left"
      >
        <DestinationImage
          destination={destination}
          width={160}
          className="size-12 shrink-0 rounded-xl"
        />
        <span className={cn("flex size-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold text-white", accentDot)}>
          {day.day}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-xs font-medium text-neutral-400">Day {day.day}</span>
          <span className="block truncate font-medium">{day.title}</span>
        </span>
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="shrink-0 text-neutral-400"
        >
          <ChevronDown className="size-5" />
        </motion.span>
      </button>

      <motion.div
        initial={false}
        animate={{ height: isOpen ? "auto" : 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="overflow-hidden"
      >
        <div className="flex flex-col gap-4 px-5 pb-5">
          {BLOCKS.map((block) => (
            <div key={block.key} className="flex gap-3">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
                <block.icon className="size-4" />
              </span>
              <div>
                <div className="text-xs font-semibold tracking-wide text-neutral-400 uppercase">{block.label}</div>
                <p className="mt-0.5 text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
                  {day[block.key]}
                </p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
