import Link from "next/link";
import { PageHeader, Card } from "@/app/components/ui";
import SearchForm from "@/app/components/search-form";

export default function NewSearchPage() {
  return (
    <div className="grid gap-6">
      <PageHeader
        title="Nuova ricerca"
        subtitle="Configura una ricerca monitorata su Vinted. Il bot confronta i prezzi tra prodotti uguali e segnala le occasioni."
        action={
          <Link href="/searches" className="btn-ghost">
            ← Tutte le ricerche
          </Link>
        }
      />
      <Card>
        <SearchForm />
      </Card>
    </div>
  );
}
