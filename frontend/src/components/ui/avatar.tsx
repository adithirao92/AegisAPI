import { ShieldCheck } from "lucide-react";

export function Avatar() {
  return (
    <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-emerald-300 to-cyan-500 text-slate-950">
      <ShieldCheck className="h-5 w-5" />
    </div>
  );
}
