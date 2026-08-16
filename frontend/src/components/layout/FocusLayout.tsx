import { Compass, X } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

export function FocusLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex h-16 shrink-0 items-center justify-between px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold tracking-tight">
          <span className="flex size-8 items-center justify-center rounded-full bg-brand-500 text-white">
            <Compass className="size-4.5" strokeWidth={2.25} />
          </span>
          TripTiers
        </Link>
        <Link
          to="/"
          aria-label="Close"
          className="flex size-11 items-center justify-center rounded-full text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-neutral-700 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
        >
          <X className="size-5" />
        </Link>
      </header>
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
