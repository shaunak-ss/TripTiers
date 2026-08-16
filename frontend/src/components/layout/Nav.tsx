import { Compass, LayoutDashboard } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { LoginDialog } from "@/components/auth/LoginDialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

export function Nav() {
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const [loginOpen, setLoginOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-white/70 backdrop-blur-md dark:bg-neutral-900/60">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold tracking-tight">
          <span className="flex size-8 items-center justify-center rounded-full bg-brand-500 text-white">
            <Compass className="size-4.5" strokeWidth={2.25} />
          </span>
          TripTiers
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {user ? (
            <Link
              to="/dashboard"
              className={cn(
                "flex min-h-11 items-center gap-1.5 rounded-full px-3.5 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800",
                location.pathname.startsWith("/dashboard") && "bg-neutral-100 dark:bg-neutral-800"
              )}
            >
              <LayoutDashboard className="size-4" />
              Dashboard
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => setLoginOpen(true)}
              className="hidden min-h-11 items-center rounded-full px-3.5 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 sm:flex dark:text-neutral-300 dark:hover:bg-neutral-800"
            >
              Log in
            </button>
          )}
          <Button
            size="lg"
            className="h-11 rounded-full"
            nativeButton={false}
            render={<Link to="/plan">Plan my trip</Link>}
          />
        </nav>
      </div>
      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </header>
  );
}
