import NewSearchForm from "@/app/components/new-search-form";

export default function NewSearchPage() {
  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <section>
        <h1 style={{ marginTop: 0 }}>Nuova ricerca</h1>
        <p style={{ color: "#94a3b8" }}>
          Configura una ricerca monitorata su Vinted: il bot confrontera i prezzi e inviera alert se trova occasioni.
        </p>
      </section>

      <section>
        <NewSearchForm />
      </section>
    </div>
  );
}
