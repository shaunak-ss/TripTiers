import { SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

export function ComparisonToggle({ active, onToggle }: { active: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={active}
      className={cn(
        "flex min-h-11 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors",
        active
          ? "border-brand-500 bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-500"
          : "border-border text-neutral-600 hover:border-brand-500/40 dark:text-neutral-300"
      )}
    >
      <SlidersHorizontal className="size-4" />
      Show differences
    </button>
  );
}
