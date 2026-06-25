import { getJobs } from "@/lib/api";
import type { JobRun } from "@/lib/api";
import { PageHeader, Card, StatusBadge, EmptyState } from "@/app/components/ui";
import { formatDateTime, formatDuration } from "@/lib/format";

export const dynamic = "force-dynamic";

/** Job details are stored as a JSON string on success; render it readably. */
function renderDetails(job: JobRun) {
  if (!job.details) return null;
  try {
    const parsed = JSON.parse(job.details) as Record<string, unknown>;
    const parts: string[] = [];
    if ("searches_processed" in parsed) parts.push(`${parsed.searches_processed} ricerche`);
    if ("deals_found" in parsed) parts.push(`${parsed.deals_found} deal`);
    if ("failed_searches" in parsed && Number(parsed.failed_searches) > 0) parts.push(`${parsed.failed_searches} errori`);
    return parts.length ? parts.join(" · ") : job.details;
  } catch {
    return job.details;
  }
}

export default async function JobsPage() {
  const jobs = await getJobs();

  return (
    <div className="grid gap-6">
      <PageHeader title="Job di scansione" subtitle="Storico delle ultime esecuzioni del monitoraggio." />

      {jobs.length === 0 ? (
        <EmptyState title="Nessun job eseguito." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Stato</th>
                <th className="px-4 py-3">Avviato</th>
                <th className="px-4 py-3">Durata</th>
                <th className="px-4 py-3">Risultato</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-b border-slate-800/60 last:border-0">
                  <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                  <td className="px-4 py-3 text-slate-300">{formatDateTime(job.started_at)}</td>
                  <td className="px-4 py-3 text-slate-400">{formatDuration(job.started_at, job.finished_at)}</td>
                  <td className="px-4 py-3 text-slate-400">{renderDetails(job) || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
