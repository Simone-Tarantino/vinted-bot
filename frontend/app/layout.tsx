import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vinted Deal Agent",
  description: "Monitor Vinted listings and compare prices online",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#0f172a", color: "#e2e8f0" }}>
        <header style={{ borderBottom: "1px solid #1e293b", padding: "1rem 1.5rem" }}>
          <nav style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
            <strong style={{ fontSize: "1.1rem" }}>Vinted Deal Agent</strong>
            <a href="/" style={{ color: "#93c5fd" }}>Dashboard</a>
            <a href="/searches/new" style={{ color: "#93c5fd" }}>Nuova ricerca</a>
            <a href="/deals" style={{ color: "#93c5fd" }}>Deals</a>
          </nav>
        </header>
        <main style={{ padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>{children}</main>
      </body>
    </html>
  );
}
