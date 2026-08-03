import { ArrowUpRight, MoreHorizontal } from "lucide-react";

import { recentScans } from "../../data/mock-dashboard";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Table, TableRow } from "../ui/table";

function riskClass(score: number) { return score >= 75 ? "text-rose-300 bg-rose-400/10" : score >= 50 ? "text-amber-300 bg-amber-400/10" : "text-emerald-300 bg-emerald-400/10"; }

export function RecentScansTable() {
  return <Card className="overflow-hidden"><div className="flex items-center justify-between border-b border-line p-5 sm:p-6"><div><p className="text-base font-semibold">Recent Scans</p><p className="mt-1 text-sm text-muted">Latest security assessment activity</p></div><Button variant="ghost" className="gap-2 text-accent">View all <ArrowUpRight className="h-4 w-4" /></Button></div><div className="overflow-x-auto"><Table className="min-w-[740px]"><thead className="bg-slate-950/25 text-xs uppercase tracking-wide text-muted"><tr><th className="px-6 py-3 font-medium">Target API</th><th className="px-4 py-3 font-medium">Type</th><th className="px-4 py-3 font-medium">Findings</th><th className="px-4 py-3 font-medium">Risk score</th><th className="px-4 py-3 font-medium">Status</th><th className="px-4 py-3 font-medium">Scanned</th><th className="px-4 py-3" /></tr></thead><tbody>{recentScans.map(scan => <TableRow key={scan.id} className="hover:bg-slate-800/30"><td className="px-6 py-4"><p className="font-medium text-slate-100">{scan.target}</p><p className="mt-0.5 text-xs text-muted">{scan.id}</p></td><td className="px-4 py-4 text-slate-300">{scan.apiType}</td><td className="px-4 py-4 font-medium">{scan.findings}</td><td className="px-4 py-4"><Badge className={riskClass(scan.riskScore)}>{scan.riskScore}/100</Badge></td><td className="px-4 py-4"><span className="inline-flex items-center gap-2 text-sm text-slate-300"><i className="h-2 w-2 rounded-full bg-accent" />{scan.status}</span></td><td className="px-4 py-4 text-slate-400">{scan.scannedAt}</td><td className="px-4 py-4"><Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button></td></TableRow>)}</tbody></Table></div></Card>;
}
