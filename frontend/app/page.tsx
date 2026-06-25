import Link from "next/link";
import { getDeals, getHealth, getJobs, getListings, getSearches } from "@/lib/api";
import { PageHeader, StatCard, Card, Badge, StatusBadge } from "@/app/components/ui";
import { formatDateTime, formatDuration } from "@/lib/format";
import ScanButton from "@/app/components/scan-button";

export const dynamic = "force-dynamic";

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
    <div className="grid gap-6">
      <PageHeader
        title="Dashboard"
        subtitle="Monitoraggio annunci Vinted con confronto prezzi tra prodotti uguali (firma prodotto) e alert Telegram."
        action={<ScanButton />}
      />

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard
          label="Stato servizio"
          value={<span className={health.status === "ok" ? "text-emerald-400" : "text-amber-400"}>{health.status}</span>}
        />
        <StatCard label="Gemini" value={health.gemini_configured ? "OK" : "Assente"} hint={health.gemini_configured ? undefined : "configura GEMINI_API_KEY"} />
        <StatCard label="Ricerche attive" value={`${activeSearches}/${searches.length}`} />
        <StatCard label="Annunci tracciati" value={listings.length} />
        <StatCard label="Deal trovati" value={deals.length} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Ultima scansione</h2>
            <Link href="/jobs" className="text-sm text-blue-400 hover:underline">
              Storico →
            </Link>
          </div>
          {latestJob ? (
            <dl className="mt-3 grid gap-2 text-sm">
              <div className="flex items-center justify-between">
                <dt className="text-slate-400">Stato</dt>
                <dd><StatusBadge status={latestJob.status} /></dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-slate-400">Avviata</dt>
                <dd className="text-slate-200">{formatDateTime(latestJob.started_at)}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-slate-400">Durata</dt>
                <dd className="text-slate-200">{formatDuration(latestJob.started_at, latestJob.finished_at)}</dd>
              </div>
              {latestJob.details ? (
                <div className="mt-1 rounded-lg bg-slate-950 p-2 text-xs text-slate-400">{latestJob.details}</div>
              ) : null}
            </dl>
          ) : (
            <p className="mt-3 text-sm text-slate-400">Nessuna scansione eseguita. Usa “Avvia scansione ora”.</p>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Ricerche monitorate</h2>
            <Link href="/searches" className="text-sm text-blue-400 hover:underline">
              Gestisci →
            </Link>
          </div>
          {searches.length === 0 ? (
            <p className="mt-3 text-sm text-slate-400">
              Nessuna ricerca. <Link href="/searches" className="text-blue-400 hover:underline">Aggiungine una</Link>.
            </p>
          ) : (
            <ul className="mt-3 grid gap-2">
              {searches.slice(0, 6).map((search) => (
                <li key={search.id} className="flex items-center justify-between gap-2 text-sm">
                  <span className="truncate text-slate-200">
                    {search.query}
                    {search.brand ? <span className="text-slate-500"> · {search.brand}</span> : null}
                  </span>
                  <Badge tone={search.is_active ? "green" : "slate"}>{search.is_active ? "attiva" : "pausa"}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>
    </div>
  );
}
