import Link from "next/link";
import LogoMono from "@/components/LogoMono";

/**
 * Lightweight nav for SSR pages that don't need auth-aware controls
 * (public archives, guides, etc). Mirrors the look of the homepage's
 * glass nav so users have a consistent escape hatch.
 */
export default function SiteNav() {
  return (
    <nav className="glass-nav sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center space-x-3">
            <LogoMono className="h-10" />
          </Link>
          <div className="hidden sm:flex items-center space-x-1 sm:space-x-2">
            <Link
              href="/"
              className="px-3 py-1.5 rounded text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5"
            >
              Home
            </Link>
            <Link
              href="/companies"
              className="px-3 py-1.5 rounded text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5"
            >
              Companies
            </Link>
            <Link
              href="/properties"
              className="px-3 py-1.5 rounded text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5"
            >
              Prospector's Exchange
            </Link>
            <Link
              href="/guides"
              className="px-3 py-1.5 rounded text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5"
            >
              Guides
            </Link>
            <Link
              href="/reports/weekly"
              className="ml-1 px-3 py-1.5 rounded text-sm font-semibold text-gold-400 hover:text-gold-300 hover:bg-gold-500/10 border border-gold-500/30"
            >
              Weekly Snapshot
            </Link>
          </div>
          <Link
            href="/"
            className="sm:hidden text-sm font-medium text-slate-200 hover:text-white"
          >
            Home
          </Link>
        </div>
      </div>
    </nav>
  );
}
