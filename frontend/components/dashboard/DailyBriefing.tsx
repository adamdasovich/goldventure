"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { dashboardAPI, watchlistAPI, companyAPI } from "@/lib/api";

/* ---------- types ---------- */

interface PriceBlock {
  latest: number;
  currency: string;
  as_of: string;
  change_pct: number | null;
}
interface NewsItem {
  title: string;
  date: string;
  type: string;
  release_type: string;
  url: string;
  is_material: boolean;
}
interface FinancingItem {
  type: string;
  amount_usd: number;
  status: string;
  date: string;
}
interface DocItem {
  title: string;
  type: string;
  date: string | null;
}
interface CompanyBlock {
  company_id: number;
  name: string;
  ticker: string;
  price: PriceBlock | null;
  news: NewsItem[];
  financings: FinancingItem[];
  documents: DocItem[];
  activity_score: number;
  has_activity: boolean;
}
interface Mover {
  company_id: number;
  ticker: string;
  name: string;
  change_pct: number;
}
interface Stats {
  movers_up: number;
  movers_down: number;
  news_count: number;
  financing_count: number;
  document_count: number;
  active_company_count: number;
  top_gainer: Mover | null;
  top_loser: Mover | null;
}
interface Briefing {
  has_watchlist: boolean;
  date: string;
  window_days: number;
  watchlist_name: string;
  company_count: number;
  headline: string | null;
  stats: Stats;
  companies: CompanyBlock[];
}

interface SearchCompany {
  id: number;
  name: string;
  ticker_symbol: string;
  exchange: string;
}

/* ---------- helpers ---------- */

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function longDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function relativeDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((today.getTime() - d.getTime()) / 86_400_000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function fmtMoney(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${Math.round(v).toLocaleString()}`;
}

function pctClass(v: number | null | undefined): string {
  if (v == null) return "text-slate-400";
  if (v > 0) return "text-emerald-400";
  if (v < 0) return "text-red-400";
  return "text-slate-300";
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}

/* ---------- watchlist manager (search + add/remove) ---------- */

function WatchlistManager({
  watched,
  accessToken,
  busy,
  onToggle,
}: {
  watched: CompanyBlock[];
  accessToken: string;
  busy: boolean;
  onToggle: (companyId: number) => void;
}) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<SearchCompany[]>([]);
  const [searching, setSearching] = useState(false);

  const watchedIds = useMemo(
    () => new Set(watched.map((c) => c.company_id)),
    [watched],
  );

  useEffect(() => {
    const q = search.trim();
    if (q.length < 2) {
      setResults([]);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const res = await companyAPI.getAll({ search: q, page_size: 8 });
        if (!cancelled) setResults(res.results || []);
      } catch {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [search]);

  return (
    <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-4 space-y-3">
      {/* current watchlist chips */}
      {watched.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {watched.map((c) => (
            <span
              key={c.company_id}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/30 text-sm text-gold-300"
            >
              {c.ticker || c.name}
              <button
                type="button"
                onClick={() => onToggle(c.company_id)}
                disabled={busy}
                className="text-gold-400/70 hover:text-gold-200 disabled:opacity-50"
                aria-label={`Remove ${c.name}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* search + add */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search a company to add to your watchlist…"
          className="w-full bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-3 py-2 focus:border-gold-500/50 focus:outline-none"
        />
        {(results.length > 0 || searching) && (
          <div className="absolute z-20 mt-1 w-full bg-slate-800 border border-slate-700 rounded-md shadow-xl max-h-64 overflow-y-auto">
            {searching && results.length === 0 && (
              <p className="px-3 py-2 text-sm text-slate-500">Searching…</p>
            )}
            {results.map((c) => {
              const already = watchedIds.has(c.id);
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => {
                    if (!already) onToggle(c.id);
                    setSearch("");
                    setResults([]);
                  }}
                  disabled={busy || already}
                  className="flex items-center justify-between w-full text-left px-3 py-2 text-sm hover:bg-slate-700/60 transition-colors disabled:opacity-50"
                >
                  <span className="text-slate-200 truncate">
                    {c.name}
                    {c.ticker_symbol && (
                      <span className="text-slate-500 ml-2">
                        {c.ticker_symbol}
                      </span>
                    )}
                  </span>
                  <span className="text-xs text-gold-400 shrink-0 ml-2">
                    {already ? "Added" : "+ Add"}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- company activity card ---------- */

function CompanyCard({ company }: { company: CompanyBlock }) {
  const change = company.price?.change_pct;
  return (
    <div className="rounded-lg bg-slate-800/40 border border-slate-700/40 p-4">
      <div className="flex items-start justify-between gap-3">
        <Link
          href={`/companies/${company.company_id}`}
          className="group min-w-0"
        >
          <p className="text-sm font-semibold text-slate-100 group-hover:text-gold-400 transition-colors truncate">
            {company.name}
          </p>
          <p className="text-xs text-slate-500">{company.ticker}</p>
        </Link>
        {company.price && (
          <div className="text-right shrink-0">
            <p className={`text-lg font-bold ${pctClass(change)}`}>
              {fmtPct(change)}
            </p>
            <p className="text-[11px] text-slate-500">
              {company.price.latest.toFixed(3)} {company.price.currency} · 1wk
            </p>
          </div>
        )}
      </div>

      {/* news */}
      {company.news.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {company.news.map((n, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                  n.is_material ? "bg-gold-400" : "bg-slate-600"
                }`}
              />
              <span className="min-w-0">
                {n.url ? (
                  <a
                    href={n.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-300 hover:text-gold-400"
                  >
                    {n.title}
                  </a>
                ) : (
                  <span className="text-slate-300">{n.title}</span>
                )}
                <span className="text-xs text-slate-500">
                  {" "}
                  · {n.type} · {relativeDate(n.date)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}

      {/* financings + documents */}
      {(company.financings.length > 0 || company.documents.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {company.financings.map((f, i) => (
            <span
              key={`f${i}`}
              className="text-xs px-2 py-1 rounded-md bg-gold-500/10 border border-gold-500/30 text-gold-300"
            >
              💰 {f.type} · {fmtMoney(f.amount_usd)}
            </span>
          ))}
          {company.documents.map((d, i) => (
            <span
              key={`d${i}`}
              className="text-xs px-2 py-1 rounded-md bg-slate-700/40 border border-slate-600/40 text-slate-300"
            >
              📄 New {d.type}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- main component ---------- */

export default function DailyBriefing() {
  const { user, accessToken } = useAuth();
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [managing, setManaging] = useState(false);
  const [busy, setBusy] = useState(false);

  const fetchBriefing = useCallback(async () => {
    if (!accessToken) return;
    try {
      const res = (await dashboardAPI.dailyBriefing(accessToken)) as Briefing;
      setBriefing(res);
    } catch (e: any) {
      setError(e?.message || "Couldn't load your briefing.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchBriefing();
  }, [fetchBriefing]);

  const handleToggle = async (companyId: number) => {
    if (!accessToken || busy) return;
    setBusy(true);
    try {
      await watchlistAPI.toggle(companyId, accessToken);
      await fetchBriefing();
    } catch {
      /* ignore */
    } finally {
      setBusy(false);
    }
  };

  const firstName = user?.full_name?.trim().split(/\s+/)[0] || "there";

  // Briefing is for signed-in users only.
  if (!accessToken) return null;

  /* ----- loading ----- */
  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6 mb-8 border border-gold-500/20">
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-48 bg-slate-700/60 rounded" />
          <div className="h-8 w-3/4 bg-slate-700/50 rounded" />
          <div className="h-20 w-full bg-slate-800/60 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !briefing) {
    return null; // fail quietly — the dashboard still works without the briefing
  }

  const activeCompanies = briefing.companies.filter((c) => c.has_activity);
  const quietCompanies = briefing.companies.filter((c) => !c.has_activity);
  const standout =
    briefing.stats.top_gainer && briefing.stats.top_gainer.change_pct >= 3
      ? briefing.stats.top_gainer
      : null;

  return (
    <div className="glass-card rounded-2xl p-6 mb-8 border border-gold-500/20 relative overflow-hidden">
      {/* subtle gold glow */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-gold-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* header */}
      <div className="relative flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-gold-400/80 mb-1">
            Daily Briefing · {longDate(briefing.date)}
          </p>
          <h2 className="text-2xl font-bold text-white">
            {greeting()}, {firstName}.
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setManaging((m) => !m)}
          className="text-sm text-slate-400 hover:text-gold-400 border border-slate-700/50 hover:border-gold-500/40 rounded-lg px-3 py-1.5 transition-all"
        >
          {managing ? "Done" : "Manage watchlist"}
        </button>
      </div>

      {/* ===== EMPTY STATE ===== */}
      {!briefing.has_watchlist ? (
        <div className="relative">
          <p className="text-slate-300 mb-1">
            Build your watchlist and this becomes your daily edge.
          </p>
          <p className="text-sm text-slate-500 mb-4 max-w-2xl">
            Add the mining companies you&apos;re tracking — we&apos;ll surface
            their price moves, news releases, financings and new technical
            reports here every time you visit. Start with a few:
          </p>
          {accessToken && (
            <WatchlistManager
              watched={[]}
              accessToken={accessToken}
              busy={busy}
              onToggle={handleToggle}
            />
          )}
          <p className="text-xs text-slate-500 mt-3">
            Tip: you can also hit the{" "}
            <span className="text-gold-400">☆ Watch</span> button on any company
            page.
          </p>
        </div>
      ) : (
        /* ===== BRIEFING STATE ===== */
        <div className="relative space-y-5">
          {/* headline */}
          {briefing.headline && (
            <p className="text-lg text-slate-200 leading-relaxed">
              {briefing.headline}
            </p>
          )}

          {/* stat strip */}
          <div className="flex flex-wrap gap-2.5">
            <Stat label={`${briefing.stats.movers_up} up`} tone="up" />
            <Stat label={`${briefing.stats.movers_down} down`} tone="down" />
            <Stat label={`${briefing.stats.news_count} news`} tone="neutral" />
            {briefing.stats.financing_count > 0 && (
              <Stat
                label={`${briefing.stats.financing_count} financing${
                  briefing.stats.financing_count > 1 ? "s" : ""
                }`}
                tone="gold"
              />
            )}
            {briefing.stats.document_count > 0 && (
              <Stat
                label={`${briefing.stats.document_count} new report${
                  briefing.stats.document_count > 1 ? "s" : ""
                }`}
                tone="neutral"
              />
            )}
            <span className="text-xs text-slate-500 self-center ml-1">
              across {briefing.company_count} watched{" "}
              {briefing.company_count === 1 ? "company" : "companies"}
            </span>
          </div>

          {/* standout mover */}
          {standout && (
            <div className="flex items-center gap-2 rounded-lg bg-gold-500/10 border border-gold-500/25 px-4 py-2.5">
              <span className="text-lg">🔥</span>
              <span className="text-sm text-slate-200">
                Standout this week —{" "}
                <Link
                  href={`/companies/${standout.company_id}`}
                  className="font-semibold text-gold-300 hover:underline"
                >
                  {standout.ticker}
                </Link>{" "}
                <span className="text-emerald-400 font-semibold">
                  {fmtPct(standout.change_pct)}
                </span>
              </span>
            </div>
          )}

          {/* manage panel */}
          {managing && accessToken && (
            <WatchlistManager
              watched={briefing.companies}
              accessToken={accessToken}
              busy={busy}
              onToggle={handleToggle}
            />
          )}

          {/* active company cards */}
          {activeCompanies.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {activeCompanies.map((c) => (
                <CompanyCard key={c.company_id} company={c} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              No notable activity across your watchlist this week — a good
              moment to scan for new ideas.
            </p>
          )}

          {/* quiet companies */}
          {quietCompanies.length > 0 && (
            <p className="text-xs text-slate-500">
              <span className="text-slate-400">Also watching:</span>{" "}
              {quietCompanies.map((c, i) => (
                <span key={c.company_id}>
                  <Link
                    href={`/companies/${c.company_id}`}
                    className="hover:text-gold-400"
                  >
                    {c.ticker || c.name}
                  </Link>
                  {i < quietCompanies.length - 1 ? " · " : ""}
                </span>
              ))}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------- stat pill ---------- */

function Stat({
  label,
  tone,
}: {
  label: string;
  tone: "up" | "down" | "gold" | "neutral";
}) {
  const dot =
    tone === "up"
      ? "bg-emerald-400"
      : tone === "down"
        ? "bg-red-400"
        : tone === "gold"
          ? "bg-gold-400"
          : "bg-slate-400";
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/70 border border-slate-700/50 text-xs text-slate-300">
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
