import { Compass } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/layout/PageTransition";

export function NotFoundPage() {
  return (
    <PageTransition>
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
        <span className="flex size-14 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-900/40">
          <Compass className="size-7" />
        </span>
        <h1 className="font-display text-2xl font-semibold">This trip took a wrong turn</h1>
        <p className="max-w-sm text-neutral-500 dark:text-neutral-400">
          We couldn't find that page. Let's get you back on route.
        </p>
        <Button
          size="lg"
          className="mt-2 h-12 rounded-full"
          nativeButton={false}
          render={<Link to="/">Back to home</Link>}
        />
      </div>
    </PageTransition>
  );
}
