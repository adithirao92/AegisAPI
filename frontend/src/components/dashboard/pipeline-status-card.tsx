import { Card } from "../ui/card";

const stages = ["Discovery", "Authentication", "Request Execution", "Vulnerability Scanning", "Risk Assessment", "Cloud Mapping", "Security Advisor", "Reporting", "Persistence"];

export function PipelineStatusCard() {
  return <Card className="p-5 sm:p-6"><p className="text-base font-semibold">Pipeline Status</p><p className="mt-1 text-sm text-muted">Latest scan processing stages</p><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">{stages.map((stage, index) => <div key={stage} className="flex items-center gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-emerald-400/15 text-xs font-bold text-accent">✓</span><div className="min-w-0 flex-1"><div className="flex justify-between gap-3"><span className="text-sm text-slate-200">{stage}</span><span className="text-xs text-accent">Complete</span></div>{index < stages.length - 1 && <div className="mt-2 h-px bg-line" />}</div></div>)}</div></Card>;
}
