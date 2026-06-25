import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-2xl text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-1 text-3xl font-bold text-white">{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
    </div>
  );
}

type BadgeTone = "green" | "amber" | "red" | "slate" | "blue";

const TONE_CLASSES: Record<BadgeTone, string> = {
  green: "bg-emerald-950/60 text-emerald-300 ring-emerald-800/60",
  amber: "bg-amber-950/60 text-amber-300 ring-amber-800/60",
  red: "bg-red-950/60 text-red-300 ring-red-800/60",
  slate: "bg-slate-800 text-slate-300 ring-slate-700",
  blue: "bg-blue-950/60 text-blue-300 ring-blue-800/60",
};

export function Badge({ tone = "slate", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}

/** Maps a JobRun.status string to a coloured badge. */
export function StatusBadge({ status }: { status: string }) {
  const tone: BadgeTone =
    status === "success" ? "green" : status === "running" ? "amber" : status === "failed" ? "red" : "slate";
  const label =
    status === "success" ? "Completato" : status === "running" ? "In corso" : status === "failed" ? "Fallito" : status;
  return <Badge tone={tone}>{label}</Badge>;
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card flex flex-col items-center justify-center gap-1 py-10 text-center">
      <p className="font-medium text-slate-300">{title}</p>
      {hint ? <p className="text-sm text-slate-500">{hint}</p> : null}
    </div>
  );
}
