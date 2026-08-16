import { AnimatePresence } from "framer-motion";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { DashboardLayout, RequireAuth } from "@/components/layout/DashboardLayout";
import { FocusLayout } from "@/components/layout/FocusLayout";
import { SiteLayout } from "@/components/layout/SiteLayout";
import { DashboardTripsPage } from "@/pages/dashboard/DashboardTripsPage";
import { InvitePage } from "@/pages/dashboard/InvitePage";
import { ProfilePage } from "@/pages/dashboard/ProfilePage";
import { RoomPage } from "@/pages/dashboard/RoomPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { GeneratingPage } from "@/pages/GeneratingPage";
import { JoinRoomPage } from "@/pages/JoinRoomPage";
import { LandingPage } from "@/pages/LandingPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PlanPage } from "@/pages/PlanPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { TierDetailPage } from "@/pages/TierDetailPage";

function routeKey(pathname: string): string {
  if (pathname.startsWith("/dashboard")) return "dashboard";
  if (pathname.startsWith("/auth/")) return "auth";
  return pathname;
}

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" initial={false}>
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
    </AnimatePresence>
  );
}

export default function App() {
  return <AnimatedRoutes />;
}
