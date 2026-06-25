import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/app/components/nav";

export const metadata: Metadata = {
  title: "Vinted Deal Agent",
  description: "Monitora annunci Vinted e confronta i prezzi tra prodotti uguali",
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%230f172a'/%3E%3Ctext x='50%25' y='55%25' dominant-baseline='middle' text-anchor='middle' font-size='32' fill='%2393c5fd'%3EV%3C/text%3E%3C/svg%3E",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <Nav />
        <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">{children}</main>
      </body>
    </html>
  );
}
