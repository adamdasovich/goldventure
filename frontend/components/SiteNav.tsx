import Link from "next/link";
import LogoMono from "@/components/LogoMono";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/companies", label: "Companies" },
  { href: "/properties", label: "Prospector's Exchange" },
  { href: "/guides", label: "Guides" },
];

const FEATURED = { href: "/reports/weekly", label: "Weekly Snapshot" };

/**
 * Lightweight nav for SSR pages that don't need auth-aware controls
 * (public archives, guides, etc). Mirrors the look of the homepage's
 * glass nav so users have a consistent escape hatch.
 *
 * Below `sm` the links move to a scrolling chip strip rather than being
 * hidden — these are the SEO archive routes, so a mobile visitor arriving
 * from search needs somewhere to go next. Kept free of client JS so the
 * report pages stay fully server-rendered.
 */
export default function SiteNav() {
  return (
    <nav className="glass-nav sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center shrink-0">
            <LogoMono className="h-10" />
          </Link>
          <div className="hidden sm:flex items-center space-x-1 sm:space-x-2">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-1.5 rounded text-sm font-medium text-slate-200 hover:text-white hover:bg-white/5"
              >
                {link.label}
              </Link>
            ))}
            <Link
              href={FEATURED.href}
              className="ml-1 px-3 py-1.5 rounded text-sm font-semibold text-gold-400 hover:text-gold-300 hover:bg-gold-500/10 border border-gold-500/30"
            >
              {FEATURED.label}
            </Link>
          </div>
        </div>

        <nav
          aria-label="Site sections"
          className="sm:hidden flex items-center gap-2 pb-3 overflow-x-auto scrollbar-none"
        >
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="px-4 py-2.5 rounded-full text-sm font-medium whitespace-nowrap border border-slate-700 text-slate-200 hover:text-white hover:border-slate-500"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href={FEATURED.href}
            className="px-4 py-2.5 rounded-full text-sm font-semibold whitespace-nowrap border border-gold-500/30 text-gold-400"
          >
            {FEATURED.label}
          </Link>
        </nav>
      </div>
    </nav>
  );
}
