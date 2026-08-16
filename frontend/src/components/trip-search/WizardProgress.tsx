import { cn } from "@/lib/utils";

const STEP_LABELS = ["Where & when", "Budget & travelers", "Review"];

export function WizardProgress({ step }: { step: 1 | 2 | 3 }) {
  return (
    <div className="mx-auto w-full max-w-lg px-4 sm:px-6">
      <div className="flex items-center gap-2">
        {STEP_LABELS.map((label, index) => {
          const stepNumber = index + 1;
          const isActive = stepNumber === step;
          const isDone = stepNumber < step;
          return (
            <div key={label} className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "h-1.5 flex-1 rounded-full transition-colors duration-300",
                  isActive || isDone ? "bg-brand-500" : "bg-neutral-200 dark:bg-neutral-800"
                )}
              />
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-center text-sm font-medium text-neutral-500 dark:text-neutral-400">
        Step {step} of 3 · {STEP_LABELS[step - 1]}
      </p>
    </div>
  );
}
