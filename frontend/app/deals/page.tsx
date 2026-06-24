import { getDeals } from "@/lib/api";

export default async function DealsPage() {
  const deals = await getDeals();

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <section>
        <h1 style={{ marginTop: 0 }}>Deal segnalati</h1>
        <p style={{ color: "#94a3b8" }}>
          Offerte Vinted sotto soglia rispetto al benchmark eBay, validate da Gemini.
        </p>
      </section>

      {deals.length === 0 ? (
        <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem" }}>
          <p style={{ margin: 0, color: "#94a3b8" }}>Nessun deal ancora rilevato.</p>
        </div>
      ) : (
        deals.map((deal) => (
          <article
            key={deal.id}
            style={{
              background: "#111827",
              border: "1px solid #1f2937",
              borderRadius: 12,
              padding: "1rem",
            }}
          >
            <h2 style={{ margin: "0 0 0.5rem", fontSize: 18 }}>
              {deal.listing?.title || `Listing #${deal.listing_id}`}
            </h2>
            <div style={{ display: "grid", gap: 4, color: "#cbd5e1" }}>
              <span>Prezzo Vinted: €{deal.vinted_price.toFixed(2)}</span>
              <span>Benchmark eBay: €{deal.benchmark_price.toFixed(2)}</span>
              <span>Sconto stimato: {deal.discount_percent.toFixed(1)}%</span>
              <span>Confidenza AI: {(deal.match_confidence * 100).toFixed(0)}%</span>
              <span>Notificato: {deal.is_notified ? "Sì" : "No"}</span>
              {deal.listing?.url ? (
                <a href={deal.listing.url} target="_blank" rel="noreferrer" style={{ color: "#93c5fd" }}>
                  Apri su Vinted
                </a>
              ) : null}
            </div>
          </article>
        ))
      )}
    </div>
  );
}
