"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type FormState = {
  query: string;
  brand: string;
  size: string;
  maxPrice: string;
  discountThresholdPercent: string;
};

const INITIAL_FORM: FormState = {
  query: "",
  brand: "",
  size: "",
  maxPrice: "",
  discountThresholdPercent: "20",
};

export default function NewSearchForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!form.query.trim()) {
      setError("La query e obbligatoria.");
      return;
    }

    const discountThresholdPercent = Number(form.discountThresholdPercent);
    if (
      Number.isNaN(discountThresholdPercent) ||
      discountThresholdPercent < 0 ||
      discountThresholdPercent > 90
    ) {
      setError("La soglia deve essere compresa tra 0 e 90.");
      return;
    }

    const maxPrice = form.maxPrice.trim() ? Number(form.maxPrice) : null;
    if (maxPrice !== null && (Number.isNaN(maxPrice) || maxPrice <= 0)) {
      setError("Il prezzo massimo deve essere un numero positivo.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/searches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: form.query.trim(),
          brand: form.brand.trim() || null,
          size: form.size.trim() || null,
          max_price: maxPrice,
          discount_threshold_percent: discountThresholdPercent,
        }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(payload?.detail || `Errore API (${response.status})`);
      }

      setForm(INITIAL_FORM);
      setSuccessMessage("Ricerca salvata con successo.");
      router.refresh();
    } catch (submissionError) {
      if (submissionError instanceof Error) {
        setError(submissionError.message);
      } else {
        setError("Errore imprevisto durante il salvataggio.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem" }}>
      <h2 style={{ marginTop: 0, fontSize: 18 }}>Nuova ricerca</h2>
      <p style={{ color: "#94a3b8", marginTop: 0 }}>
        Aggiungi una ricerca monitorata da Vinted con soglia sconto personalizzata.
      </p>

      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Query *</span>
          <input
            type="text"
            value={form.query}
            onChange={(event) => setForm((current) => ({ ...current, query: event.target.value }))}
            placeholder="es. nike air max 90"
            required
            style={{
              padding: "0.6rem",
              borderRadius: 8,
              border: "1px solid #334155",
              background: "#0f172a",
              color: "#e2e8f0",
            }}
          />
        </label>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Brand</span>
            <input
              type="text"
              value={form.brand}
              onChange={(event) => setForm((current) => ({ ...current, brand: event.target.value }))}
              placeholder="es. Nike"
              style={{
                padding: "0.6rem",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#e2e8f0",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Taglia</span>
            <input
              type="text"
              value={form.size}
              onChange={(event) => setForm((current) => ({ ...current, size: event.target.value }))}
              placeholder="es. 42"
              style={{
                padding: "0.6rem",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#e2e8f0",
              }}
            />
          </label>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Prezzo massimo (EUR)</span>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.maxPrice}
              onChange={(event) => setForm((current) => ({ ...current, maxPrice: event.target.value }))}
              placeholder="es. 80"
              style={{
                padding: "0.6rem",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#e2e8f0",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Soglia sconto (%)</span>
            <input
              type="number"
              min="0"
              max="90"
              step="1"
              value={form.discountThresholdPercent}
              onChange={(event) =>
                setForm((current) => ({ ...current, discountThresholdPercent: event.target.value }))
              }
              style={{
                padding: "0.6rem",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#e2e8f0",
              }}
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            width: "fit-content",
            padding: "0.6rem 1rem",
            borderRadius: 8,
            border: "1px solid #3b82f6",
            background: isSubmitting ? "#1e3a8a" : "#2563eb",
            color: "#ffffff",
            cursor: isSubmitting ? "default" : "pointer",
          }}
        >
          {isSubmitting ? "Salvataggio..." : "Aggiungi ricerca"}
        </button>
      </form>

      {error ? <p style={{ color: "#f87171", marginBottom: 0 }}>{error}</p> : null}
      {successMessage ? <p style={{ color: "#34d399", marginBottom: 0 }}>{successMessage}</p> : null}
    </div>
  );
}
