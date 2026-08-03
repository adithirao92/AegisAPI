// import { DashboardLayout } from "./layouts/dashboard-layout";

// export default function App() {
//   return <DashboardLayout />;
// }
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { DashboardPage } from "./pages/dashboard-page";
import { NewScanPage } from "./pages/new-scan-page";
import { ReportsPage } from "./pages/reports-page";
import { ScanHistoryPage } from "./pages/scan-history-page";
import { SettingsPage } from "./pages/settings-page";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/new-scan" element={<NewScanPage />} />
        <Route path="/history" element={<ScanHistoryPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
