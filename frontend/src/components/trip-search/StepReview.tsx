import { CalendarDays, MapPin, Plane, Users, Wallet } from "lucide-react";
import { useFormContext } from "react-hook-form";
import { formatDateRange } from "@/lib/dates";
import { formatCurrency } from "@/lib/format";
import type { TripSearchFormValues } from "@/lib/schema";

interface ReviewRow {
  icon: typeof MapPin;
  label: string;
  value: string;
  step: 1 | 2;
}

export function StepReview({ onEditStep }: { onEditStep: (step: 1 | 2) => void }) {
  const { watch } = useFormContext<TripSearchFormValues>();
  const values = watch();

  const rows: ReviewRow[] = [
    { icon: Plane, label: "Flying from", value: values.originCity || "—", step: 1 },
    { icon: MapPin, label: "Destination", value: values.destination || "—", step: 1 },
    {
      icon: CalendarDays,
      label: "Dates",
      value: values.startDate && values.endDate ? formatDateRange(values.startDate, values.endDate) : "—",
      step: 1,
    },
    { icon: Wallet, label: "Budget", value: formatCurrency(values.budget ?? 0), step: 2 },
    {
      icon: Users,
      label: "Travelers",
      value: `${values.travelers ?? 1} ${(values.travelers ?? 1) === 1 ? "traveler" : "travelers"}`,
      step: 2,
    },
  ];

  return (
    <div className="flex flex-col gap-3">
      {rows.map((row) => (
        <button
          key={row.label}
          type="button"
          onClick={() => onEditStep(row.step)}
          className="group flex min-h-16 w-full items-center gap-4 rounded-xl border border-border px-4 py-3 text-left transition-colors hover:border-brand-500/50 hover:bg-brand-50/50 dark:hover:bg-brand-900/10"
        >
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
            <row.icon className="size-4.5" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-xs font-medium text-neutral-400">{row.label}</span>
            <span className="block truncate font-medium">{row.value}</span>
          </span>
          <span className="shrink-0 text-xs font-medium text-brand-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-brand-500">
            Edit
          </span>
        </button>
      ))}
    </div>
  );
}
