import { useState, type ReactNode } from "react";

import { AppSidebar } from "../components/dashboard/app-sidebar";
import { TopNavbar } from "../components/dashboard/top-navbar";

export function DashboardLayout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-canvas lg:flex">
      <AppSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-w-0 flex-1 px-4 py-5 sm:px-7 sm:py-7 xl:px-9">
        <TopNavbar onMenuClick={() => setSidebarOpen(true)} />

        {children}
      </main>
    </div>
  );
}
