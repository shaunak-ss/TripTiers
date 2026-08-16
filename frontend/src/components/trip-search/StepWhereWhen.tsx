import { useFormContext } from "react-hook-form";
import { FieldError } from "@/components/trip-search/FieldError";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { TripSearchFormValues } from "@/lib/schema";
import { cn } from "@/lib/utils";

const POPULAR_DESTINATIONS = [
  "Bali, Indonesia",
  "Tokyo, Japan",
  "Lisbon, Portugal",
  "Paris, France",
  "Bangkok, Thailand",
  "Santorini, Greece",
  "Dubai, UAE",
  "New York, USA",
];

export function StepWhereWhen() {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = useFormContext<TripSearchFormValues>();

  const destination = watch("destination");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Label htmlFor="originCity">Flying from</Label>
        <Input
          id="originCity"
          placeholder="e.g. New Delhi"
          className="mt-2 h-12 rounded-xl text-base"
          {...register("originCity")}
        />
        <FieldError message={errors.originCity?.message} />
      </div>

      <div>
        <Label htmlFor="destination">Where to?</Label>
        <Input
          id="destination"
          placeholder="e.g. Bali, Indonesia"
          className="mt-2 h-12 rounded-xl text-base"
          {...register("destination")}
        />
        <FieldError message={errors.destination?.message} />

        <div className="mt-3 flex flex-wrap gap-2">
          {POPULAR_DESTINATIONS.map((place) => (
            <button
              key={place}
              type="button"
              onClick={() => setValue("destination", place, { shouldValidate: true, shouldDirty: true })}
              className={cn(
                "min-h-11 rounded-full border px-3.5 text-sm font-medium transition-colors",
                destination === place
                  ? "border-brand-500 bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-500"
                  : "border-border text-neutral-600 hover:border-brand-500/50 hover:bg-brand-50 dark:text-neutral-300 dark:hover:bg-brand-900/20"
              )}
            >
              {place}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="startDate">Departure</Label>
          <Input
            id="startDate"
            type="date"
            className="mt-2 h-12 rounded-xl text-base"
            {...register("startDate")}
          />
          <FieldError message={errors.startDate?.message} />
        </div>
        <div>
          <Label htmlFor="endDate">Return</Label>
          <Input id="endDate" type="date" className="mt-2 h-12 rounded-xl text-base" {...register("endDate")} />
          <FieldError message={errors.endDate?.message} />
        </div>
      </div>
    </div>
  );
}
