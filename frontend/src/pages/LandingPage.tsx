import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { ArrowRight, ListChecks, MapPinned, Sparkles } from "lucide-react";
import { useRef } from "react";
import { Link } from "react-router-dom";
import { PageTransition } from "@/components/layout/PageTransition";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/format";
import { fadeUp, staggerContainer, staggerItem } from "@/lib/motion";
import { TIER_META, TIER_ORDER } from "@/lib/tiers";

const previewPricing: Record<(typeof TIER_ORDER)[number], { price: number; flight: string; stay: string }> = {
  backpacker: { price: 980, flight: "Budget combo via KUL", stay: "Canggu social hostel" },
  comfort: { price: 1650, flight: "One-stop via Singapore", stay: "Ubud jungle pool villa" },
  luxury: { price: 3400, flight: "Business class via SIN", stay: "Four Seasons Sayan villa" },
};

const howItWorks = [
  {
    icon: MapPinned,
    title: "Tell us your trip",
    description: "Destination, dates, and a rough budget — that's it. Takes under a minute.",
  },
  {
    icon: ListChecks,
    title: "We compare everything",
    description: "Real flights across dozens of airlines, matched to three complete ways to travel.",
  },
  {
    icon: Sparkles,
    title: "Pick your version",
    description: "Backpacker, Comfort, or Luxury — see the full trip, then book the one that fits.",
  },
];

export function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const backgroundY = useTransform(scrollYProgress, [0, 1], [0, shouldReduceMotion ? 0 : 20]);

  return (
    <PageTransition>
      <div>
        {/* Hero */}
        <section ref={heroRef} className="relative overflow-hidden">
          <motion.div
            style={{ y: backgroundY }}
            className="animate-gradient-shift absolute inset-0 -z-10 bg-[linear-gradient(120deg,var(--color-brand-50)_0%,var(--background)_35%,var(--color-brand-100)_70%,var(--color-brand-50)_100%)] bg-[length:200%_200%] opacity-70"
            aria-hidden
          />

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="mx-auto flex max-w-4xl flex-col items-center px-4 pt-20 pb-16 text-center sm:px-6 sm:pt-28 sm:pb-24"
          >
            <motion.div variants={staggerItem}>
              <Badge variant="secondary" className="rounded-full px-3 py-1 text-xs font-medium">
                
              </Badge>
            </motion.div>

            <motion.h1
              variants={staggerItem}
              className="mt-6 max-w-3xl font-display text-4xl leading-tight font-semibold tracking-tight sm:text-5xl md:text-6xl"
            >
              One trip. <span className="text-brand-500">Three ways</span> to take it.
            </motion.h1>

            <motion.p
              variants={staggerItem}
              className="mt-5 max-w-xl text-base leading-relaxed text-neutral-600 sm:text-lg"
            >
              Give us your destination and dates — we'll hand back a Backpacker, Comfort, and Luxury version of the
              same trip, each with a real flight and a full day-by-day plan, so you pick, not plan.
            </motion.p>

            <motion.div variants={staggerItem} whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }} className="mt-8">
              <Button
                size="lg"
                className="h-14 rounded-full px-8 text-base shadow-lg shadow-brand-500/20"
                nativeButton={false}
                render={<Link to="/plan" />}
              >
                Plan my trip
                <ArrowRight className="size-5" />
              </Button>
            </motion.div>
          </motion.div>
        </section>

        {/* Preview cards */}
        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
          <motion.div variants={fadeUp} initial="hidden" animate="show" className="mb-8 text-center">
            <p className="text-sm font-medium tracking-wide text-brand-600 uppercase"></p>
            <h2 className="mt-2 font-display text-2xl font-semibold sm:text-3xl">
              See the shape of the decision before you even search
            </h2>
          </motion.div>

          <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-5 sm:grid-cols-3">
            {TIER_ORDER.map((tierId) => {
              const meta = TIER_META[tierId];
              const preview = previewPricing[tierId];
              const Icon = meta.icon;
              const isComfort = tierId === "comfort";
              return (
                <motion.div
                  key={tierId}
                  variants={staggerItem}
                  whileHover={{ y: -3 }}
                  className={`relative flex flex-col gap-4 rounded-2xl border p-6 shadow-lg shadow-black/5 transition-shadow ${meta.border} ${meta.bg} ${
                    isComfort ? "lg:scale-105" : ""
                  }`}
                >
                  {isComfort && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white shadow-sm">
                      Most travelers pick this
                    </span>
                  )}
                  <div className="flex items-center gap-2">
                    <span className={`flex size-9 items-center justify-center rounded-full ${meta.bg}`}>
                      <Icon className={`size-5 ${meta.text}`} strokeWidth={2.25} />
                    </span>
                    <span className="font-display text-lg font-semibold">{meta.label}</span>
                  </div>
                  <div>
                    <div className="font-display text-3xl font-semibold">{formatCurrency(preview.price)}</div>
                    <div className="text-xs text-neutral-500">total for 2 travelers</div>
                  </div>
                  <ul className="space-y-1.5 text-sm text-neutral-600">
                    <li>✈️ {preview.flight}</li>
                    <li>🏨 {preview.stay}</li>
                  </ul>
                </motion.div>
              );
            })}
          </motion.div>
        </section>

        {/* How it works */}
        <section className="border-t border-border/60 bg-neutral-50 py-16">
          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <motion.h2
              variants={fadeUp}
              initial="hidden"
              animate="show"
              className="text-center font-display text-2xl font-semibold sm:text-3xl"
            >
              How it works
            </motion.h2>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
              className="mt-10 grid gap-8 sm:grid-cols-3"
            >
              {howItWorks.map((step, index) => (
                <motion.div key={step.title} variants={staggerItem} className="flex flex-col items-center text-center">
                  <span className="flex size-12 items-center justify-center rounded-full bg-brand-500/10 text-brand-500">
                    <step.icon className="size-6" strokeWidth={2} />
                  </span>
                  <span className="mt-3 text-xs font-semibold tracking-wide text-neutral-400 uppercase">
                    Step {index + 1}
                  </span>
                  <h3 className="mt-1 font-display text-lg font-semibold">{step.title}</h3>
                  <p className="mt-2 max-w-64 text-sm leading-relaxed text-neutral-500">{step.description}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      </div>
    </PageTransition>
  );
}
