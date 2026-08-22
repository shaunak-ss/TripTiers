import { AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { DashboardLayout, RequireAuth } from "@/components/layout/DashboardLayout";
import { FocusLayout } from "@/components/layout/FocusLayout";
import { SiteLayout } from "@/components/layout/SiteLayout";

const DashboardTripsPage = lazy(() =>
  import("@/pages/dashboard/DashboardTripsPage").then((m) => ({ default: m.DashboardTripsPage }))
);
const InvitePage = lazy(() => import("@/pages/dashboard/InvitePage").then((m) => ({ default: m.InvitePage })));
const ProfilePage = lazy(() => import("@/pages/dashboard/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const RoomPage = lazy(() => import("@/pages/dashboard/RoomPage").then((m) => ({ default: m.RoomPage })));
const AuthCallbackPage = lazy(() =>
  import("@/pages/AuthCallbackPage").then((m) => ({ default: m.AuthCallbackPage }))
);
const GeneratingPage = lazy(() => import("@/pages/GeneratingPage").then((m) => ({ default: m.GeneratingPage })));
const JoinRoomPage = lazy(() => import("@/pages/JoinRoomPage").then((m) => ({ default: m.JoinRoomPage })));
const LandingPage = lazy(() => import("@/pages/LandingPage").then((m) => ({ default: m.LandingPage })));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));
const PlanPage = lazy(() => import("@/pages/PlanPage").then((m) => ({ default: m.PlanPage })));
const ResultsPage = lazy(() => import("@/pages/ResultsPage").then((m) => ({ default: m.ResultsPage })));
const TierDetailPage = lazy(() => import("@/pages/TierDetailPage").then((m) => ({ default: m.TierDetailPage })));

function routeKey(pathname: string): string {
  if (pathname.startsWith("/dashboard")) return "dashboard";
  if (pathname.startsWith("/auth/")) return "auth";
  return pathname;
}

function RouteFallback() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Loader2 className="size-6 animate-spin text-neutral-400" />
    </div>
  );
}

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <Suspense fallback={<RouteFallback />}>
        <Routes location={location} key={routeKey(location.pathname)}>
          <Route element={<SiteLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/results/:tripId" element={<ResultsPage />} />
            <Route path="/results/:tripId/:tier" element={<TierDetailPage />} />
            <Route path="/trips" element={<Navigate to="/dashboard" replace />} />
            <Route path="/join/:code" element={<JoinRoomPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
          </Route>
          <Route element={<FocusLayout />}>
            <Route path="/plan" element={<PlanPage />} />
            <Route path="/plan/generating" element={<GeneratingPage />} />
          </Route>
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <DashboardLayout />
              </RequireAuth>
            }
          >
            <Route index element={<DashboardTripsPage />} />
            <Route path="invite" element={<InvitePage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="rooms/:code" element={<RoomPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </AnimatePresence>
  );
}

export default function App() {
  return <AnimatedRoutes />;
}
