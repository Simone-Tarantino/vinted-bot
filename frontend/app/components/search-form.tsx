"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { Search } from "@/lib/api";

type Props = {
  /** When provided the form edits this search (PATCH); otherwise it creates one (POST). */
  search?: Search;
  onDone?: () => void;
  onCancel?: () => void;
};

type FormState = {
  query: string;
  brand: string;
  size: string;
  maxPrice: string;
  discountThresholdPercent: string;
};

function toFormState(search?: Search): FormState {
  return {
    query: search?.query ?? "",
    brand: search?.brand ?? "",
    size: search?.size ?? "",
    maxPrice: search?.max_price != null ? String(search.max_price) : "",
    discountThresholdPercent: search ? String(search.discount_threshold_percent) : "20",
  };
}

export default function SearchForm({ search, onDone, onCancel }: Props) {
  const router = useRouter();
  const isEdit = Boolean(search);
  const [form, setForm] = useState<FormState>(() => toFormState(search));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!form.query.trim()) {
      setError("La query è obbligatoria.");
      return;
    }

    const discountThresholdPercent = Number(form.discountThresholdPercent);
    if (Number.isNaN(discountThresholdPercent) || discountThresholdPercent < 0 || discountThresholdPercent > 90) {
      setError("La soglia deve essere compresa tra 0 e 90.");
      return;
    }

    const maxPrice = form.maxPrice.trim() ? Number(form.maxPrice) : null;
    if (maxPrice !== null && (Number.isNaN(maxPrice) || maxPrice <= 0)) {
      setError("Il prezzo massimo deve essere un numero positivo.");
      return;
    }

    const payload = {
      query: form.query.trim(),
      brand: form.brand.trim() || null,
      size: form.size.trim() || null,
      max_price: maxPrice,
      discount_threshold_percent: discountThresholdPercent,
    };

    setIsSubmitting(true);
    try {
      const response = await fetch(isEdit ? `/api/searches/${search!.id}` : "/api/searches", {
        method: isEdit ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const detail = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(detail?.detail || `Errore API (${response.status})`);
      }

      if (!isEdit) setForm(toFormState());
      router.refresh();
      onDone?.();
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Errore imprevisto.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-3">
      <label className="grid gap-1.5">
        <span className="text-sm text-slate-300">Cosa cercare *</span>
        <input
          type="text"
          className="field"
          value={form.query}
          onChange={(e) => update("query", e.target.value)}
          placeholder="es. carte pokemon serie 1"
          required
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="text-sm text-slate-300">Brand</span>
          <input type="text" className="field" value={form.brand} onChange={(e) => update("brand", e.target.value)} placeholder="opzionale" />
        </label>
        <label className="grid gap-1.5">
          <span className="text-sm text-slate-300">Taglia</span>
          <input type="text" className="field" value={form.size} onChange={(e) => update("size", e.target.value)} placeholder="opzionale" />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="text-sm text-slate-300">Prezzo massimo (€)</span>
          <input
            type="number"
            step="0.01"
            min="0"
            className="field"
            value={form.maxPrice}
            onChange={(e) => update("maxPrice", e.target.value)}
            placeholder="nessun limite"
          />
        </label>
        <label className="grid gap-1.5">
          <span className="text-sm text-slate-300">Soglia sconto (%)</span>
          <input
            type="number"
            min="0"
            max="90"
            step="1"
            className="field"
            value={form.discountThresholdPercent}
            onChange={(e) => update("discountThresholdPercent", e.target.value)}
          />
        </label>
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <div className="flex gap-2">
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? "Salvataggio…" : isEdit ? "Salva modifiche" : "Aggiungi ricerca"}
        </button>
        {onCancel ? (
          <button type="button" className="btn-ghost" onClick={onCancel} disabled={isSubmitting}>
            Annulla
          </button>
        ) : null}
      </div>
    </form>
  );
}
