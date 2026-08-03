import { useState } from "react";

import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Table, TableRow } from "../components/ui/table";
import { PageHeader } from "../components/shared/page-header";
import { DashboardLayout } from "../layouts/dashboard-layout";

const scans = [["Customer API", "Jul 21, 2026", "REST", "82", "4", "Completed"], ["Payments GraphQL", "Jul 20, 2026", "GraphQL", "71", "2", "Completed"], ["Identity Service", "Jul 19, 2026", "REST", "42", "0", "Completed"], ["Partner Gateway", "Jul 18, 2026", "REST", "35", "0", "Completed"]];

export function ScanHistoryPage() {
  const [query, setQuery] = useState("");
  const rows = scans.filter(([name]) => name.toLowerCase().includes(query.toLowerCase()));
  return <DashboardLayout><PageHeader title="Scan History" description="Review completed mock scan activity." action={<Button>New Scan</Button>} /><Card className="overflow-hidden"><div className="flex flex-wrap gap-3 border-b border-line p-5"><Input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search scan name..." className="max-w-sm" /><select className="h-10 rounded-lg border border-line bg-slate-900 px-3 text-sm text-slate-300"><option>All API types</option><option>REST</option><option>GraphQL</option></select><select className="h-10 rounded-lg border border-line bg-slate-900 px-3 text-sm text-slate-300"><option>All statuses</option><option>Completed</option></select></div><div className="overflow-x-auto"><Table className="min-w-[800px]"><thead className="bg-slate-950/25 text-xs uppercase tracking-wide text-muted"><tr>{["Scan Name", "Date", "API Type", "Risk Score", "Critical Findings", "Status", "Actions"].map(title => <th key={title} className="px-5 py-3 text-left font-medium">{title}</th>)}</tr></thead><tbody>{rows.map(([name, date, type, risk, critical, status]) => <TableRow key={name}><td className="px-5 py-4 font-medium">{name}</td><td className="px-5 py-4 text-muted">{date}</td><td className="px-5 py-4">{type}</td><td className="px-5 py-4"><Badge className={Number(risk) > 70 ? "bg-rose-400/10 text-rose-300" : "bg-emerald-400/10 text-emerald-300"}>{risk}/100</Badge></td><td className="px-5 py-4">{critical}</td><td className="px-5 py-4"><span className="text-accent">●</span> <span className="text-slate-300">{status}</span></td><td className="px-5 py-4"><div className="flex gap-2"><Button variant="outline" className="h-8 px-3 text-xs">View</Button><Button variant="ghost" className="h-8 px-3 text-xs text-rose-300">Delete</Button></div></td></TableRow>)}</tbody></Table></div><div className="flex items-center justify-between border-t border-line p-4 text-sm text-muted"><span>Showing {rows.length} of {scans.length} scans</span><div className="flex gap-2"><Button variant="outline" className="h-8 px-3 text-xs">Previous</Button><Button variant="outline" className="h-8 px-3 text-xs">Next</Button></div></div></Card></DashboardLayout>;
}
