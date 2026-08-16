import { Minus, Plus } from "lucide-react";
import { Controller, useFormContext } from "react-hook-form";
import { FieldError } from "@/components/trip-search/FieldError";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { formatCurrency } from "@/lib/format";
import type { TripSearchFormValues } from "@/lib/schema";

const MIN_BUDGET = 200;
const MAX_BUDGET = 10000;
const MAX_TRAVELERS = 12;

export function StepBudgetTravelers() {
  const {
    control,
    formState: { errors },
  } = useFormContext<TripSearchFormValues>();

  return (
    <div className="flex flex-col gap-10">
      <Controller
        control={control}
        name="budget"
        render={({ field }) => (
          <div>
            <div className="flex items-baseline justify-between">
              <Label htmlFor="budget-slider">Total budget</Label>
              <span className="font-display text-2xl font-semibold text-brand-600 dark:text-brand-500">
                {formatCurrency(field.value ?? MIN_BUDGET)}
              </span>
            </div>
            <Slider
              id="budget-slider"
              className="mt-5"
              min={MIN_BUDGET}
              max={MAX_BUDGET}
              step={50}
              value={[field.value ?? MIN_BUDGET]}
              onValueChange={(value) => field.onChange(Array.isArray(value) ? value[0] : value)}
            />
            <div className="mt-2 flex justify-between text-xs text-neutral-400">
              <span>{formatCurrency(MIN_BUDGET)}</span>
              <span>{formatCurrency(MAX_BUDGET)}+</span>
            </div>
            <FieldError message={errors.budget?.message} />
          </div>
        )}
      />

      <Controller
        control={control}
        name="travelers"
        render={({ field }) => (
          <div>
            <Label>Travelers</Label>
            <div className="mt-3 flex items-center gap-4">
              <button
                type="button"
                aria-label="Fewer travelers"
                onClick={() => field.onChange(Math.max(1, (field.value ?? 1) - 1))}
                className="flex size-11 items-center justify-center rounded-full border border-border text-neutral-600 transition-colors hover:border-brand-500 hover:text-brand-600 disabled:opacity-40 dark:text-neutral-300"
                disabled={(field.value ?? 1) <= 1}
              >
                <Minus className="size-4" />
              </button>
              <span className="w-12 text-center font-display text-2xl font-semibold tabular-nums">
                {field.value ?? 1}
              </span>
              <button
                type="button"
                aria-label="More travelers"
                onClick={() => field.onChange(Math.min(MAX_TRAVELERS, (field.value ?? 1) + 1))}
                className="flex size-11 items-center justify-center rounded-full border border-border text-neutral-600 transition-colors hover:border-brand-500 hover:text-brand-600 disabled:opacity-40 dark:text-neutral-300"
                disabled={(field.value ?? 1) >= MAX_TRAVELERS}
              >
                <Plus className="size-4" />
              </button>
              <span className="text-sm text-neutral-500 dark:text-neutral-400">
                {(field.value ?? 1) === 1 ? "traveler" : "travelers"}
              </span>
            </div>
            <FieldError message={errors.travelers?.message} />
          </div>
        )}
      />
    </div>
  );
}
