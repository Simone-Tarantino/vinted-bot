import { getListings } from "@/lib/api";
import { PageHeader, Card, Badge, EmptyState } from "@/app/components/ui";
import { formatEuro, formatDateTime } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ListingsPage() {
  const listings = await getListings();

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Annunci tracciati"
        subtitle={`${listings.length} annunci monitorati, dal più recente.`}
      />

      {listings.length === 0 ? (
        <EmptyState title="Nessun annuncio tracciato." hint="Verranno popolati alla prossima scansione." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing) => (
            <Card key={listing.id} className="flex flex-col gap-2 p-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {listing.image_url ? (
                <img
                  src={listing.image_url}
                  alt={listing.title}
                  className="h-40 w-full rounded-lg object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="grid h-40 w-full place-items-center rounded-lg bg-slate-950 text-sm text-slate-600">
                  nessuna immagine
                </div>
              )}
              <h3 className="line-clamp-2 text-sm font-medium text-slate-100">{listing.title}</h3>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-white">{formatEuro(listing.price)}</span>
                {listing.condition ? <Badge>{listing.condition}</Badge> : null}
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Visto: {formatDateTime(listing.last_seen_at)}</span>
                <a href={listing.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                  Apri ↗
                </a>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
