"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ScanButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "err"; text: string } | null>(null);

  async function runScan() {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/scan", { method: "POST" });
      const payload = (await response.json().catch(() => null)) as { status?: string; detail?: string } | null;
      if (!response.ok) throw new Error(payload?.detail || `Errore API (${response.status})`);

      if (payload?.status === "triggered") {
        setMessage({ tone: "ok", text: "Scansione avviata. I risultati appariranno tra poco." });
      } else {
        setMessage({ tone: "err", text: "Scheduler non pronto, riprova tra qualche secondo." });
      }
      // Give the backend a moment to record the new job, then refresh the stats.
      setTimeout(() => router.refresh(), 2500);
    } catch (e) {
      setMessage({ tone: "err", text: e instanceof Error ? e.message : "Errore imprevisto." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button className="btn-primary" onClick={runScan} disabled={busy}>
        {busy ? "Avvio…" : "Avvia scansione ora"}
      </button>
      {message ? (
        <span className={`text-xs ${message.tone === "ok" ? "text-emerald-400" : "text-red-400"}`}>{message.text}</span>
      ) : null}
    </div>
  );
}
