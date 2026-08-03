import { CriticalFindingsTable } from "../components/dashboard/critical-findings-table";
import { KpiCard } from "../components/dashboard/kpi-card";
import { PipelineStatusCard } from "../components/dashboard/pipeline-status-card";
import { RecentScansTable } from "../components/dashboard/recent-scans-table";
import { RiskTrendChart } from "../components/dashboard/risk-trend-chart";
import { SeverityChart } from "../components/dashboard/severity-chart";
import { kpiMetrics } from "../data/mock-dashboard";
import { DashboardLayout } from "../layouts/dashboard-layout";

export function DashboardPage() {
  return <DashboardLayout><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{kpiMetrics.map(metric => <KpiCard key={metric.label} metric={metric} />)}</div><div className="mt-4 grid gap-4 xl:grid-cols-[1.35fr_0.9fr]"><SeverityChart /><RiskTrendChart /></div><div className="mt-4"><RecentScansTable /></div><div className="mt-4 grid gap-4 xl:grid-cols-[1.35fr_0.9fr]"><CriticalFindingsTable /><PipelineStatusCard /></div></DashboardLayout>;
}
