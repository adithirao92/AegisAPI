import { Activity, AlertTriangle, Gauge, Network } from "lucide-react";

import { Card } from "../ui/card";
import type { KpiMetric } from "../../types/dashboard";

const iconByLabel = { "APIs Scanned": Network, "Total Findings": Activity, "Critical Findings": AlertTriangle, "Average Risk Score": Gauge };
const toneClass = { emerald: "bg-emerald-400/10 text-emerald-300", violet: "bg-violet-400/10 text-violet-300", rose: "bg-rose-400/10 text-rose-300", amber: "bg-amber-400/10 text-amber-300" };

export function KpiCard({ metric }: { metric: KpiMetric }) {
  const Icon = iconByLabel[metric.label as keyof typeof iconByLabel];
  return <Card className="p-5"><div className="flex items-start justify-between"><div><p className="text-sm text-muted">{metric.label}</p><p className="mt-3 text-3xl font-semibold tracking-tight">{metric.value}</p></div><div className={`rounded-xl p-2.5 ${toneClass[metric.tone]}`}><Icon className="h-5 w-5" /></div></div><p className="mt-4 text-xs text-slate-400">{metric.trend}</p></Card>;
}
