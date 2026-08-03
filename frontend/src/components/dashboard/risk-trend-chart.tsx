import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { riskTrendData } from "../../data/mock-dashboard";
import { Card } from "../ui/card";

export function RiskTrendChart() {
  return <Card className="min-h-[360px] p-5 sm:p-6"><div className="flex items-start justify-between"><div><p className="text-base font-semibold">Risk Trend</p><p className="mt-1 text-sm text-muted">Average normalized risk score</p></div><span className="rounded-lg bg-emerald-400/10 px-2 py-1 text-xs font-medium text-accent">−12% weekly</span></div><div className="mt-6 h-60"><ResponsiveContainer width="100%" height="100%"><AreaChart data={riskTrendData} margin={{ left: -16, right: 4, top: 8 }}><defs><linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#56d5a1" stopOpacity={0.35} /><stop offset="100%" stopColor="#56d5a1" stopOpacity={0} /></linearGradient></defs><CartesianGrid vertical={false} stroke="#263142" strokeDasharray="3 3" /><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: "#8793a6", fontSize: 12 }} /><YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fill: "#8793a6", fontSize: 12 }} /><Tooltip contentStyle={{ background: "#111720", border: "1px solid #263142", borderRadius: 12 }} /><Area type="monotone" dataKey="score" stroke="#56d5a1" strokeWidth={3} fill="url(#riskGradient)" /></AreaChart></ResponsiveContainer></div></Card>;
}
