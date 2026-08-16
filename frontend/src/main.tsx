import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MotionConfig } from "framer-motion";
import { ThemeProvider } from "next-themes";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/components/auth/AuthProvider";
import App from "./App.tsx";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* reducedMotion="user" makes every Framer Motion animation in the app
        respect prefers-reduced-motion automatically, falling back to opacity-only. */}
    <MotionConfig reducedMotion="user">
      <ThemeProvider attribute="class" forcedTheme="light" defaultTheme="light">
        <TooltipProvider delay={200}>
          <BrowserRouter>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
          <Toaster position="bottom-center" />
        </TooltipProvider>
      </ThemeProvider>
    </MotionConfig>
  </StrictMode>
);
