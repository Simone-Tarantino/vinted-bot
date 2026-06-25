"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Search } from "@/lib/api";
import { Badge } from "@/app/components/ui";
import SearchForm from "@/app/components/search-form";

function SearchRow({ search }: { search: Search }) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [busy, setBusy] = useState<null | "toggle" | "delete">(null);
  const [error, setError] = useState<string | null>(null);

  async function mutate(action: "toggle" | "delete") {
    setError(null);
    setBusy(action);
    try {
      const response = await fetch(`/api/searches/${search.id}`, {
        method: action === "delete" ? "DELETE" : "PATCH",
        headers: action === "toggle" ? { "Content-Type": "application/json" } : undefined,
        body: action === "toggle" ? JSON.stringify({ is_active: !search.is_active }) : undefined,
      });
      if (!response.ok) {
        const detail = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(detail?.detail || `Errore API (${response.status})`);
      }
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore imprevisto.");
    } finally {
      setBusy(null);
    }
  }

  async function onDelete() {
    if (!window.confirm(`Eliminare la ricerca "${search.query}"? L'operazione non è reversibile.`)) return;
    await mutate("delete");
  }

  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-lg font-semibold text-white">{search.query}</h3>
            <Badge tone={search.is_active ? "green" : "slate"}>{search.is_active ? "Attiva" : "In pausa"}</Badge>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
            {search.brand ? <Badge tone="blue">Brand: {search.brand}</Badge> : null}
            {search.size ? <Badge tone="blue">Taglia: {search.size}</Badge> : null}
            {search.max_price != null ? <Badge>Max €{search.max_price}</Badge> : null}
            <Badge>Soglia {search.discount_threshold_percent}%</Badge>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <button className="btn-ghost" onClick={() => mutate("toggle")} disabled={busy !== null}>
            {busy === "toggle" ? "…" : search.is_active ? "Pausa" : "Attiva"}
          </button>
          <button className="btn-ghost" onClick={() => setIsEditing((v) => !v)} disabled={busy !== null}>
            {isEditing ? "Chiudi" : "Modifica"}
          </button>
          <button className="btn-danger" onClick={onDelete} disabled={busy !== null}>
            {busy === "delete" ? "…" : "Elimina"}
          </button>
        </div>
      </div>

      {error ? <p className="mt-3 text-sm text-red-400">{error}</p> : null}

      {isEditing ? (
        <div className="mt-4 border-t border-slate-800 pt-4">
          <SearchForm search={search} onDone={() => setIsEditing(false)} onCancel={() => setIsEditing(false)} />
        </div>
      ) : null}
    </div>
  );
}

export default function SearchManager({ searches }: { searches: Search[] }) {
  const [creating, setCreating] = useState(false);

  return (
    <div className="grid gap-4">
      <div className="card">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-white">Nuova ricerca</h2>
            <p className="text-sm text-slate-400">Aggiungi un prodotto da monitorare su Vinted.</p>
          </div>
          <button className={creating ? "btn-ghost" : "btn-primary"} onClick={() => setCreating((v) => !v)}>
            {creating ? "Chiudi" : "+ Aggiungi"}
          </button>
        </div>
        {creating ? (
          <div className="mt-4 border-t border-slate-800 pt-4">
            <SearchForm onDone={() => setCreating(false)} onCancel={() => setCreating(false)} />
          </div>
        ) : null}
      </div>

      {searches.length === 0 ? (
        <div className="card text-center text-slate-400">Nessuna ricerca configurata. Aggiungine una qui sopra.</div>
      ) : (
        searches.map((search) => <SearchRow key={search.id} search={search} />)
      )}
    </div>
  );
}
