import { getDeals, getHealth, getJobs, getListings, getSearches } from "@/lib/api";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: 12,
        padding: "1rem",
      }}
    >
      <div style={{ color: "#94a3b8", fontSize: 14 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>{value}</div>
    </div>
  );
}

export default async function DashboardPage() {
  const [health, searches, listings, deals, jobs] = await Promise.all([
    getHealth(),
    getSearches(),
    getListings(),
    getDeals(),
    getJobs(),
  ]);

  const activeSearches = searches.filter((s) => s.is_active).length;
  const latestJob = jobs[0];

  return (
    <div style={{ display: "grid", gap: "1.5rem" }}>
      <section>
        <h1 style={{ marginTop: 0 }}>Dashboard</h1>
        <p style={{ color: "#94a3b8" }}>
          Monitoraggio automatico Vinted con confronto prezzi eBay e matching AI Gemini.
        </p>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
        <StatCard label="Stato servizio" value={health.status} />
        <StatCard label="Gemini configurato" value={health.gemini_configured ? "Sì" : "No"} />
        <StatCard label="Ricerche attive" value={activeSearches} />
        <StatCard label="Listing tracciati" value={listings.length} />
        <StatCard label="Deal trovati" value={deals.length} />
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: 18 }}>Ultimo job</h2>
          {latestJob ? (
            <ul style={{ paddingLeft: 18, margin: 0, color: "#cbd5e1" }}>
              <li>Nome: {latestJob.job_name}</li>
              <li>Stato: {latestJob.status}</li>
              <li>Avviato: {new Date(latestJob.started_at).toLocaleString("it-IT")}</li>
              <li>Dettagli: {latestJob.details || "-"}</li>
            </ul>
          ) : (
            <p style={{ color: "#94a3b8" }}>Nessun job eseguito.</p>
          )}
        </div>

        <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: 18 }}>Ricerche monitorate</h2>
          {searches.length === 0 ? (
            <p style={{ color: "#94a3b8" }}>Nessuna ricerca configurata.</p>
          ) : (
            <ul style={{ paddingLeft: 18, margin: 0, color: "#cbd5e1" }}>
              {searches.slice(0, 8).map((search) => (
                <li key={search.id}>
                  {search.query}
                  {search.brand ? ` (${search.brand})` : ""} - soglia {search.discount_threshold_percent}%
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
