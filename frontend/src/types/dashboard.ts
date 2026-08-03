export type Severity = "Critical" | "High" | "Medium" | "Low";

export interface KpiMetric {
  label: string;
  value: string;
  trend: string;
  tone: "emerald" | "violet" | "rose" | "amber";
}

export interface RecentScan {
  id: string;
  target: string;
  apiType: "REST" | "GraphQL";
  findings: number;
  riskScore: number;
  status: "Completed" | "In progress";
  scannedAt: string;
}
