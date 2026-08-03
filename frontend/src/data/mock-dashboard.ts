import type { KpiMetric, RecentScan, Severity } from "../types/dashboard";

export const kpiMetrics: KpiMetric[] = [
  { label: "APIs Scanned", value: "128", trend: "+12.5% this month", tone: "emerald" },
  { label: "Total Findings", value: "346", trend: "+18 from last scan", tone: "violet" },
  { label: "Critical Findings", value: "12", trend: "4 need immediate action", tone: "rose" },
  { label: "Average Risk Score", value: "62", trend: "8% lower than last month", tone: "amber" }
];

export const severityData: Array<{ name: Severity; value: number; color: string }> = [
  { name: "Critical", value: 12, color: "#fb7185" },
  { name: "High", value: 48, color: "#f59e0b" },
  { name: "Medium", value: 126, color: "#8b5cf6" },
  { name: "Low", value: 160, color: "#38bdf8" }
];

export const riskTrendData = [
  { day: "Mon", score: 74 }, { day: "Tue", score: 69 }, { day: "Wed", score: 72 },
  { day: "Thu", score: 64 }, { day: "Fri", score: 67 }, { day: "Sat", score: 60 },
  { day: "Sun", score: 62 }
];

export const recentScans: RecentScan[] = [
  { id: "scan-9842", target: "Customer API", apiType: "REST", findings: 28, riskScore: 82, status: "Completed", scannedAt: "2 min ago" },
  { id: "scan-9839", target: "Payments GraphQL", apiType: "GraphQL", findings: 17, riskScore: 71, status: "Completed", scannedAt: "1 hr ago" },
  { id: "scan-9835", target: "Identity Service", apiType: "REST", findings: 9, riskScore: 42, status: "Completed", scannedAt: "Yesterday" },
  { id: "scan-9832", target: "Partner Gateway", apiType: "REST", findings: 6, riskScore: 35, status: "Completed", scannedAt: "Jul 18" }
];
