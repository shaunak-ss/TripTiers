import { Backpack, Gem, Sparkles } from "lucide-react";
import type { TierId } from "@/types/trip";

export const TIER_ORDER: TierId[] = ["backpacker", "comfort", "luxury"];

export const TIER_META: Record<
  TierId,
  {
    label: string;
    tagline: string;
    icon: typeof Backpack;
    color: string;
    bg: string;
    border: string;
    ring: string;
    text: string;
    dot: string;
  }
> = {
  backpacker: {
    label: "Backpacker",
    tagline: "See it all, spend less",
    icon: Backpack,
    color: "var(--color-tier-backpacker)",
    bg: "bg-tier-backpacker/10",
    border: "border-tier-backpacker/30",
    ring: "ring-tier-backpacker/40",
    text: "text-tier-backpacker",
    dot: "bg-tier-backpacker",
  },
  comfort: {
    label: "Comfort",
    tagline: "The sweet spot",
    icon: Sparkles,
    color: "var(--color-tier-comfort)",
    bg: "bg-tier-comfort/10",
    border: "border-tier-comfort/30",
    ring: "ring-tier-comfort/40",
    text: "text-tier-comfort",
    dot: "bg-tier-comfort",
  },
  luxury: {
    label: "Luxury",
    tagline: "Go all in",
    icon: Gem,
    color: "var(--color-tier-luxury)",
    bg: "bg-tier-luxury/10",
    border: "border-tier-luxury/30",
    ring: "ring-tier-luxury/40",
    text: "text-tier-luxury",
    dot: "bg-tier-luxury",
  },
};
