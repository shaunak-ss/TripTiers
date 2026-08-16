import { Outlet } from "react-router-dom";
import { Footer } from "@/components/layout/Footer";
import { Nav } from "@/components/layout/Nav";

export function SiteLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <Nav />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
