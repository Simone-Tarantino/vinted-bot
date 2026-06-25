import { getDeals } from "@/lib/api";
import { PageHeader, Card, Badge, EmptyState } from "@/app/components/ui";
import { formatEuro, formatDateTime } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DealsPage() {
  const deals = await getDeals();

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Deal segnalati"
        subtitle="Annunci il cui prezzo è sotto la mediana degli annunci dello stesso prodotto (firma prodotto) su Vinted."
      />

      {deals.length === 0 ? (
        <EmptyState title="Nessun deal ancora rilevato." hint="Avvia una scansione dalla Dashboard per popolare i risultati." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {deals.map((deal) => (
            <Card key={deal.id} className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <h2 className="text-base font-semibold text-white">{deal.listing?.title || `Annuncio #${deal.listing_id}`}</h2>
                <Badge tone={deal.is_notified ? "green" : "slate"}>{deal.is_notified ? "Notificato" : "Non notificato"}</Badge>
              </div>

              <div className="flex items-end gap-3">
                <div>
                  <div className="text-xs text-slate-400">Prezzo</div>
                  <div className="text-2xl font-bold text-emerald-400">{formatEuro(deal.vinted_price)}</div>
                </div>
                <div className="pb-1 text-sm text-slate-400 line-through">{formatEuro(deal.benchmark_price)}</div>
                <Badge tone="green">−{deal.discount_percent.toFixed(0)}%</Badge>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Media stesso prodotto: {formatEuro(deal.benchmark_price)}</span>
                <span>{formatDateTime(deal.created_at)}</span>
              </div>

              {deal.listing?.url ? (
                <a href={deal.listing.url} target="_blank" rel="noreferrer" className="btn-primary w-fit">
                  Apri su Vinted ↗
                </a>
              ) : null}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
