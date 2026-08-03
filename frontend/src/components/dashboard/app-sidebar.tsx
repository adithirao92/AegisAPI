import { BarChart3, FileText, LayoutDashboard, PlusCircle, Settings, X } from "lucide-react";
import { NavLink } from "react-router-dom";

import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/dashboard" },
  { label: "New Scan", icon: PlusCircle, to: "/new-scan" },
  { label: "Scan History", icon: BarChart3, to: "/history" },
  { label: "Reports", icon: FileText, to: "/reports" },
  { label: "Settings", icon: Settings, to: "/settings" }
];

interface AppSidebarProps { open: boolean; onClose: () => void; }

export function AppSidebar({ open, onClose }: AppSidebarProps) {
  return (
    <>
      {open && <button aria-label="Close menu" onClick={onClose} className="fixed inset-0 z-30 bg-black/65 lg:hidden" />}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-line bg-[#0d1219] p-5 transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="mb-10 flex items-center justify-between px-2">
          <div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-xl bg-accent font-black text-slate-950">A</div><span className="text-lg font-semibold">AegisAPI</span></div>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose}><X className="h-5 w-5" /></Button>
        </div>
        <nav className="space-y-1">
          {navigation.map(({ label, icon: Icon, to }) => <NavLink key={label} to={to} onClick={onClose} className={({ isActive }) => cn("flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 hover:translate-x-1", isActive ? "bg-emerald-400/10 text-accent shadow-[inset_3px_0_0_#56d5a1]" : "text-muted hover:bg-slate-800 hover:text-slate-100")}><Icon className="h-5 w-5" />{label}</NavLink>)}
        </nav>
        <div className="mt-auto rounded-xl border border-line bg-slate-900/70 p-4"><p className="text-xs font-semibold text-slate-300">Security posture</p><p className="mt-2 text-2xl font-semibold text-accent">82%</p><p className="mt-1 text-xs text-muted">Healthy across 128 APIs</p></div>
      </aside>
    </>
  );
}
