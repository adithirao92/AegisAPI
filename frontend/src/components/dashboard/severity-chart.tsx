import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { severityData } from "../../data/mock-dashboard";
import { Card } from "../ui/card";

export function SeverityChart() {
  return <Card className="min-h-[360px] p-5 sm:p-6"><div><p className="text-base font-semibold">Severity Distribution</p><p className="mt-1 text-sm text-muted">Findings grouped by impact level</p></div><div className="mt-2 flex h-56 items-center"><ResponsiveContainer width="58%" height="100%"><PieChart><Pie data={severityData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} paddingAngle={4} stroke="none">{severityData.map(item => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip contentStyle={{ background: "#111720", border: "1px solid #263142", borderRadius: 12 }} /></PieChart></ResponsiveContainer><div className="space-y-3">{severityData.map(item => <div key={item.name} className="flex min-w-28 items-center justify-between gap-5 text-sm"><span className="flex items-center gap-2 text-slate-300"><i className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />{item.name}</span><span className="font-medium text-white">{item.value}</span></div>)}</div></div><div className="border-t border-line pt-4 text-sm text-muted"><span className="font-medium text-slate-100">346 total findings</span><span className="mx-2">·</span>12 critical require attention</div></Card>;
}
