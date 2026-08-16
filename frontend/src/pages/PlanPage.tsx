import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { StepBudgetTravelers } from "@/components/trip-search/StepBudgetTravelers";
import { StepReview } from "@/components/trip-search/StepReview";
import { StepWhereWhen } from "@/components/trip-search/StepWhereWhen";
import { WizardProgress } from "@/components/trip-search/WizardProgress";
import { Button } from "@/components/ui/button";
import { tripSearchSchema, type TripSearchFormValues } from "@/lib/schema";
import { wizardStepVariants } from "@/lib/motion";
import { useTripStore } from "@/store/tripStore";

const STEP_FIELDS: Record<1 | 2, (keyof TripSearchFormValues)[]> = {
  1: ["originCity", "destination", "startDate", "endDate"],
  2: ["budget", "travelers"],
};

const STEP_TITLES: Record<1 | 2 | 3, { title: string; subtitle: string }> = {
  1: { title: "Where & when?", subtitle: "Tell us the trip you're dreaming about." },
  2: { title: "What's the budget?", subtitle: "A rough number is all we need." },
  3: { title: "Ready to search?", subtitle: "Double-check the details, then find your trips." },
};

export function PlanPage() {
  const navigate = useNavigate();
  const setSearchInput = useTripStore((state) => state.setSearchInput);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [direction, setDirection] = useState<1 | -1>(1);

  const form = useForm<TripSearchFormValues>({
    resolver: zodResolver(tripSearchSchema),
    mode: "onChange",
    defaultValues: {
      destination: "",
      originCity: "",
      startDate: "",
      endDate: "",
      budget: 1500,
      travelers: 2,
    },
  });

  const goToStep = (nextStep: 1 | 2 | 3, dir: 1 | -1) => {
    setDirection(dir);
    setStep(nextStep);
  };

  const handleContinue = async () => {
    if (step === 3) return;
    const fields = STEP_FIELDS[step];
    const valid = await form.trigger(fields);
    if (valid) goToStep((step + 1) as 1 | 2 | 3, 1);
  };

  const handleBack = () => {
    if (step === 1) return;
    goToStep((step - 1) as 1 | 2 | 3, -1);
  };

  const onSubmit = form.handleSubmit((data) => {
    setSearchInput(data);
    navigate("/plan/generating");
  });

  return (
    <div className="flex flex-1 flex-col">
      <WizardProgress step={step} />

      <FormProvider {...form}>
        <form
          onSubmit={step === 3 ? onSubmit : (e) => e.preventDefault()}
          className="mx-auto flex w-full max-w-lg flex-1 flex-col px-4 pt-8 pb-28 sm:px-6"
        >
          <AnimatePresence mode="wait" custom={direction} initial={false}>
            <motion.div
              key={step}
              custom={direction}
              variants={wizardStepVariants(direction)}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            >
              <h1 className="font-display text-2xl font-semibold sm:text-3xl">{STEP_TITLES[step].title}</h1>
              <p className="mt-1.5 text-neutral-500 dark:text-neutral-400">{STEP_TITLES[step].subtitle}</p>

              <div className="mt-8">
                {step === 1 && <StepWhereWhen />}
                {step === 2 && <StepBudgetTravelers />}
                {step === 3 && <StepReview onEditStep={(s) => goToStep(s, -1)} />}
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border/60 bg-white/80 px-4 py-4 backdrop-blur-md sm:px-6 dark:bg-neutral-900/80">
            <div className="mx-auto flex max-w-lg items-center gap-3">
              {step > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  className="h-14 shrink-0 rounded-full px-5"
                  onClick={handleBack}
                >
                  <ArrowLeft className="size-5" />
                </Button>
              )}
              {step < 3 ? (
                <Button type="button" size="lg" className="h-14 w-full rounded-full text-base" onClick={handleContinue}>
                  Continue
                  <ArrowRight className="size-5" />
                </Button>
              ) : (
                <Button type="submit" size="lg" className="h-14 w-full rounded-full text-base">
                  Find my trips
                  <ArrowRight className="size-5" />
                </Button>
              )}
            </div>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}
