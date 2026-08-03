import { Badge } from "../ui/badge";
import { Card } from "../ui/card";
import { Table, TableRow } from "../ui/table";

const findings = [
  ["Critical", "/api/v1/users/{id}", "BOLA", "92", "Open"],
  ["Critical", "/api/v1/auth/login", "Broken Authentication", "88", "Open"],
  ["High", "/api/v1/payments", "Mass Assignment", "76", "Investigating"]
];

export function CriticalFindingsTable() {
  return <Card className="overflow-hidden"><div className="border-b border-line p-5 sm:p-6"><p className="text-base font-semibold">Recent Critical Findings</p><p className="mt-1 text-sm text-muted">Highest-risk vulnerabilities across recent scans</p></div><div className="overflow-x-auto"><Table className="min-w-[680px]"><thead className="bg-slate-950/25 text-xs uppercase tracking-wide text-muted"><tr>{["Severity", "Endpoint", "Vulnerability", "Risk Score", "Status"].map(label => <th key={label} className="px-5 py-3 text-left font-medium">{label}</th>)}</tr></thead><tbody>{findings.map(([severity, endpoint, vulnerability, score, status]) => <TableRow key={endpoint}><td className="px-5 py-4"><Badge className={severity === "Critical" ? "bg-rose-400/10 text-rose-300" : "bg-amber-400/10 text-amber-300"}>{severity}</Badge></td><td className="px-5 py-4 font-mono text-xs text-slate-300">{endpoint}</td><td className="px-5 py-4 text-slate-200">{vulnerability}</td><td className="px-5 py-4 font-semibold text-slate-100">{score}/100</td><td className="px-5 py-4 text-sm text-slate-300"><span className="mr-2 inline-block h-2 w-2 rounded-full bg-rose-400" />{status}</td></TableRow>)}</tbody></Table></div></Card>;
}
