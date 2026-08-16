import { Compass, LogOut, Luggage, Menu, MessageSquarePlus, UserRound } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { LoginDialog } from "@/components/auth/LoginDialog";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const NAV_ITEMS = [
  { to: "/dashboard", label: "My trips", icon: Luggage, end: true },
  { to: "/dashboard/invite", label: "Invite friends to join room", icon: MessageSquarePlus, end: false },
  { to: "/dashboard/profile", label: "Change user profile", icon: UserRound, end: false },
] as const;

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col">
      <Link to="/" className="flex items-center gap-2 px-4 py-5 font-display text-lg font-semibold tracking-tight">
        <span className="flex size-8 items-center justify-center rounded-full bg-brand-500 text-white">
          <Compass className="size-4.5" strokeWidth={2.25} />
        </span>
        TripTiers
      </Link>

      {user && (
        <div className="mx-3 mb-4 flex items-center gap-3 rounded-2xl bg-neutral-50 px-3 py-3 dark:bg-neutral-800/60">
          <span
            className="flex size-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
            style={{ backgroundColor: `hsl(${user.avatarHue} 70% 42%)` }}
          >
            {user.name.slice(0, 1).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{user.name}</p>
            <p className="truncate text-xs text-neutral-500">{user.email}</p>
          </div>
        </div>
      )}

      <nav className="flex flex-1 flex-col gap-1 px-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800",
                  isActive && "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-400"
                )
              }
            >
              <Icon className="size-4 shrink-0" />
              <span className="leading-snug">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3">
        <button
          type="button"
          onClick={() => {
            void logout().then(() => {
              onNavigate?.();
              navigate("/");
            });
          }}
          className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm font-medium text-neutral-600 transition-colors hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          <LogOut className="size-4" />
          Logout
        </button>
      </div>
    </div>
  );
}

export function DashboardLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-dvh bg-background">
      <aside className="sticky top-0 hidden h-dvh w-72 shrink-0 flex-col border-r border-border/70 bg-white md:flex dark:bg-neutral-950">
        <SidebarNav />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-border/60 bg-white/80 px-3 backdrop-blur-md md:hidden dark:bg-neutral-900/80">
          <Button variant="ghost" size="icon" className="size-11" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="size-5" />
          </Button>
          <span className="font-display font-semibold">Dashboard</span>
        </header>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="left" className="w-72 p-0" showCloseButton={false}>
            <SheetTitle className="sr-only">Dashboard menu</SheetTitle>
            <SidebarNav onNavigate={() => setOpen(false)} />
          </SheetContent>
        </Sheet>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function RequireAuth({ children }: { children?: ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const initialized = useAuthStore((state) => state.initialized);
  const [loginOpen, setLoginOpen] = useState(false);

  useEffect(() => {
    if (initialized && !user) setLoginOpen(true);
  }, [initialized, user]);

  if (!initialized) {
    return <div className="min-h-dvh bg-background" />;
  }

  if (!user) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-3 px-6 text-center">
        <h1 className="font-display text-2xl font-semibold">Log in to open your dashboard</h1>
        <p className="max-w-sm text-sm text-neutral-500">
          My trips, invite rooms, and group itineraries live here after you sign in.
        </p>
        <Button size="lg" className="h-12 rounded-full" onClick={() => setLoginOpen(true)}>
          Log in
        </Button>
        <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
      </div>
    );
  }

  return <>{children ?? <Outlet />}</>;
}
