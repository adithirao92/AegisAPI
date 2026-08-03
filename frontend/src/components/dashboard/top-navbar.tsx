import { Bell, Menu, Search } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useState } from "react";

import { Avatar } from "../ui/avatar";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

export function TopNavbar({ onMenuClick }: { onMenuClick: () => void }) {
  const [profileOpen, setProfileOpen] = useState(false);
  const { pathname } = useLocation();
  const pageLabel = { "/dashboard": "Security overview", "/new-scan": "New scan", "/history": "Scan history", "/reports": "Reports", "/settings": "Settings" }[pathname] ?? "Security overview";
  return <header className="relative flex flex-wrap items-center justify-between gap-4 pb-7"><div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenuClick}><Menu className="h-5 w-5" /></Button><div><p className="text-xs font-medium uppercase tracking-[0.18em] text-accent">{pageLabel}</p><h1 className="mt-1 text-2xl font-semibold tracking-tight">Project AegisAPI</h1></div></div><div className="flex flex-1 items-center justify-end gap-3"><div className="relative hidden w-full max-w-sm md:block"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" /><Input aria-label="Search" placeholder="Search scans, findings..." className="pl-9" /></div><Link to="/new-scan"><Button className="hidden sm:inline-flex">Run Scan</Button></Link><Button variant="ghost" size="icon" aria-label="Notifications" className="relative"><Bell className="h-5 w-5" /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-400" /></Button><button onClick={() => setProfileOpen(value => !value)} className="flex items-center gap-2 rounded-xl border border-line bg-slate-900/60 p-1.5 pr-3"><Avatar /><span className="hidden text-sm font-medium sm:block">Adithi</span></button>{profileOpen && <div className="absolute right-0 top-14 z-20 w-44 rounded-xl border border-line bg-panel p-1.5 text-sm shadow-panel"><button className="w-full rounded-lg px-3 py-2 text-left text-slate-300 hover:bg-slate-800">Profile settings</button><button className="w-full rounded-lg px-3 py-2 text-left text-slate-300 hover:bg-slate-800">Sign out</button></div>}</div></header>;
}
