import { useState } from "react";

import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { PageHeader } from "../components/shared/page-header";
import { DashboardLayout } from "../layouts/dashboard-layout";

const reports = [{ name: "Customer API Security Report", date: "Jul 21, 2026", risk: "Critical" }, { name: "Payments GraphQL Assessment", date: "Jul 20, 2026", risk: "High" }, { name: "Identity Service Report", date: "Jul 19, 2026", risk: "Medium" }];

export function ReportsPage() {
  const [selected, setSelected] = useState(0);
  return <DashboardLayout><PageHeader title="Security Reports" description="Select a mock report to review its available deliverables." /><div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]"><div className="space-y-3">{reports.map((report, index) => <button key={report.name} onClick={() => setSelected(index)} className={`w-full rounded-2xl border p-5 text-left transition-colors ${selected === index ? "border-emerald-400/50 bg-emerald-400/[0.06]" : "border-line bg-panel hover:bg-slate-800/70"}`}><p className="font-medium">{report.name}</p><p className="mt-2 text-sm text-muted">{report.date} · <span className={report.risk === "Critical" ? "text-rose-300" : "text-amber-300"}>{report.risk} risk</span></p></button>)}</div><Card className="p-6"><p className="text-xs font-medium uppercase tracking-[0.18em] text-accent">Selected report</p><h2 className="mt-2 text-xl font-semibold">{reports[selected].name}</h2><p className="mt-2 text-sm text-muted">Mock report summary with scanner findings, risk assessments, and cloud security recommendations.</p><div className="mt-7 grid gap-3 sm:grid-cols-3"><div className="rounded-xl border border-line bg-slate-900/50 p-4"><p className="text-xs text-muted">Findings</p><p className="mt-2 text-2xl font-semibold">28</p></div><div className="rounded-xl border border-line bg-slate-900/50 p-4"><p className="text-xs text-muted">Risk Score</p><p className="mt-2 text-2xl font-semibold">82</p></div><div className="rounded-xl border border-line bg-slate-900/50 p-4"><p className="text-xs text-muted">Advisories</p><p className="mt-2 text-2xl font-semibold">14</p></div></div><div className="mt-7 flex flex-wrap gap-3"><Button>View Report</Button><Button variant="outline">Download JSON</Button><Button variant="outline">Download PDF</Button></div></Card></div></DashboardLayout>;
}
