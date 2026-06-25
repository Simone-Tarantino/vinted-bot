"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/searches", label: "Ricerche" },
  { href: "/deals", label: "Deal" },
  { href: "/listings", label: "Annunci" },
  { href: "/jobs", label: "Job" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Nav() {
  const pathname = usePathname() || "/";

  return (
    <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-1 px-4 py-3 sm:px-6">
        <Link href="/" className="mr-3 flex items-center gap-2 font-semibold text-white">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand text-sm text-white">V</span>
          <span className="hidden sm:inline">Vinted Deal Agent</span>
        </Link>
        {LINKS.map((link) => {
          const active = isActive(pathname, link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                active ? "bg-slate-800 font-medium text-white" : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
