import { getSearches } from "@/lib/api";
import { PageHeader } from "@/app/components/ui";
import SearchManager from "@/app/components/search-manager";

export const dynamic = "force-dynamic";

export default async function SearchesPage() {
  const searches = await getSearches();

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Ricerche monitorate"
        subtitle="Crea, modifica, metti in pausa o elimina le ricerche. Ogni ricerca attiva viene controllata a ogni scansione."
      />
      <SearchManager searches={searches} />
    </div>
  );
}
