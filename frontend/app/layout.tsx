import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Vinted Deal Agent",
  description: "Monitor Vinted listings and compare prices online",
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%230f172a'/%3E%3Ctext x='50%25' y='55%25' dominant-baseline='middle' text-anchor='middle' font-size='32' fill='%2393c5fd'%3EV%3C/text%3E%3C/svg%3E",
  },
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
