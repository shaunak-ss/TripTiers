import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { pageTransition, pageTransitionConfig } from "@/lib/motion";

export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={pageTransition.initial}
      animate={pageTransition.animate}
      exit={pageTransition.exit}
      transition={pageTransitionConfig}
    >
      {children}
    </motion.div>
  );
}
