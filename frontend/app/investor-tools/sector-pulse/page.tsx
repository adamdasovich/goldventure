"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import { toolsAPI } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Metal {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  updated: string;
}

interface Breadth {
  date: string;
  total_stocks: number;
  up: number;
  down: number;
  flat: number;
  up_pct: number;
  avg_change_pct: number;
}

interface Mover {
  company_id: number;
  company_name: string;
  ticker: string;
  price: number;
  change_pct: number;
}

interface FinancingData {
  count_30d: number;
  total_usd_30d: number;
}

interface NewsData {
  press_releases_7d: number;
  articles_7d: number;
}

interface SectorPulseData {
  metals: Metal[];
  breadth: Breadth;
  gainers: Mover[];
  losers: Mover[];
  financing: FinancingData;
  news: NewsData;
  timestamp: string;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatUSD(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function formatPrice(n: number): string {
  return n >= 100
    ? `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : `$${n.toFixed(2)}`;
}

function changeBadge(pct: number) {
  const positive = pct > 0;
  const zero = pct === 0;
  const arrow = positive ? "\u25B2" : zero ? "\u2013" : "\u25BC";
  const color = positive
    ? "text-emerald-400"
    : zero
      ? "text-slate-400"
      : "text-red-400";
  return (
    <span className={`${color} font-semibold text-sm`}>
      {arrow} {Math.abs(pct).toFixed(2)}%
    </span>
  );
}

const METAL_ICONS: Record<string, string> = {
  Gold: "XAU",
  Silver: "XAG",
  Platinum: "XPT",
  Palladium: "XPD",
};

/* ------------------------------------------------------------------ */
/*  Skeleton                                                           */
/* ------------------------------------------------------------------ */

function Skeleton() {
  return (
    <div className="min-h-screen bg-slate-900 animate-pulse">
      {/* skeleton nav */}
      <div className="h-16 glass-nav" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        {/* header skeleton */}
        <div className="text-center space-y-3">
          <div className="h-5 w-24 bg-slate-700/60 rounded mx-auto" />
          <div className="h-9 w-72 bg-slate-700/60 rounded mx-auto" />
          <div className="h-4 w-96 bg-slate-700/40 rounded mx-auto" />
        </div>

        {/* metals row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-card rounded-xl p-5 h-28" />
          ))}
        </div>

        {/* middle row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="glass-card rounded-xl p-5 h-64" />
          <div className="glass-card rounded-xl p-5 h-64" />
          <div className="glass-card rounded-xl p-5 h-64" />
        </div>

        {/* bottom row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="glass-card rounded-xl p-5 h-36" />
          <div className="glass-card rounded-xl p-5 h-36" />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Donut Chart (CSS-only)                                             */
/* ------------------------------------------------------------------ */

function DonutChart({
  up,
  down,
  flat,
}: {
  up: number;
  down: number;
  flat: number;
}) {
  const total = up + down + flat || 1;
  const upPct = (up / total) * 100;
  const downPct = (down / total) * 100;
  // flat fills the remainder

  // conic-gradient segments: up (green), down (red), flat (slate)
  const gradient = `conic-gradient(
    #34d399 0% ${upPct}%,
    #f87171 ${upPct}% ${upPct + downPct}%,
    #64748b ${upPct + downPct}% 100%
  )`;

  return (
    <div className="relative w-40 h-40 mx-auto">
      <div
        className="w-full h-full rounded-full"
        style={{ background: gradient }}
      />
      {/* inner cutout */}
      <div className="absolute inset-4 rounded-full bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <span className="text-xl font-bold text-emerald-400">
            {upPct.toFixed(0)}%
          </span>
          <p className="text-[10px] text-slate-400 mt-0.5">advancing</p>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function SectorPulsePage() {
  const [data, setData] = useState<SectorPulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await toolsAPI.sectorPulse();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load sector data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <Skeleton />;

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="glass-card rounded-xl p-8 text-center max-w-md">
          <p className="text-red-400 text-lg font-semibold mb-2">
            Unable to load Sector Pulse
          </p>
          <p className="text-slate-400 text-sm mb-4">{error}</p>
          <Button variant="secondary" size="sm" onClick={fetchData}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Nav */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/investor-tools">
                <Button variant="ghost" size="sm">
                  All Tools
                </Button>
              </Link>
              <Link href="/">
                <Button variant="ghost" size="sm">
                  Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-3">
            Dashboard
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-3">
            Sector Pulse
          </h1>
          <p className="text-slate-300 max-w-xl mx-auto">
            Real-time overview of the junior mining sector — metals prices,
            market breadth, top movers, financing activity, and news volume.
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* ============================================================= */}
        {/*  Metals Prices                                                 */}
        {/* ============================================================= */}
        <section>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Metals Prices
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {data.metals.map((m) => (
              <div
                key={m.symbol}
                className="glass-card rounded-xl p-5 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-500 font-medium">
                    {METAL_ICONS[m.name] || m.symbol}
                  </span>
                  {changeBadge(m.change_pct)}
                </div>
                <p className="text-2xl font-bold text-slate-100">
                  {formatPrice(m.price)}
                </p>
                <p className="text-sm text-gold-400 font-medium mt-1">
                  {m.name}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ============================================================= */}
        {/*  Market Breadth + Gainers + Losers                             */}
        {/* ============================================================= */}
        <section>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Market Breadth */}
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Market Breadth
              </h2>
              <DonutChart
                up={data.breadth.up}
                down={data.breadth.down}
                flat={data.breadth.flat}
              />
              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                <div>
                  <span className="block text-emerald-400 font-bold text-base">
                    {data.breadth.up}
                  </span>
                  <span className="text-slate-500">Up</span>
                </div>
                <div>
                  <span className="block text-red-400 font-bold text-base">
                    {data.breadth.down}
                  </span>
                  <span className="text-slate-500">Down</span>
                </div>
                <div>
                  <span className="block text-slate-400 font-bold text-base">
                    {data.breadth.flat}
                  </span>
                  <span className="text-slate-500">Flat</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-700/50 text-center">
                <span className="text-xs text-slate-500">Avg Change</span>
                <p className="text-lg font-bold">
                  {changeBadge(data.breadth.avg_change_pct)}
                </p>
              </div>
              <p className="text-[10px] text-slate-600 text-center mt-1">
                {data.breadth.total_stocks} stocks tracked
              </p>
            </div>

            {/* Top 5 Gainers */}
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Top 5 Gainers
              </h2>
              <ul className="space-y-3">
                {data.gainers.map((g, i) => (
                  <li key={g.company_id}>
                    <Link
                      href={`/companies/${g.company_id}`}
                      className="flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-xs text-slate-600 w-4 shrink-0">
                          {i + 1}.
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm text-slate-200 truncate group-hover:text-gold-400 transition-colors">
                            {g.company_name}
                          </p>
                          <p className="text-xs text-slate-500">{g.ticker}</p>
                        </div>
                      </div>
                      <div className="text-right shrink-0 ml-2">
                        <p className="text-sm text-slate-300">
                          {formatPrice(g.price)}
                        </p>
                        <span className="text-xs font-semibold text-emerald-400">
                          +{g.change_pct.toFixed(2)}%
                        </span>
                      </div>
                    </Link>
                  </li>
                ))}
                {data.gainers.length === 0 && (
                  <li className="text-sm text-slate-500 text-center py-4">
                    No data available
                  </li>
                )}
              </ul>
            </div>

            {/* Top 5 Losers */}
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Top 5 Losers
              </h2>
              <ul className="space-y-3">
                {data.losers.map((l, i) => (
                  <li key={l.company_id}>
                    <Link
                      href={`/companies/${l.company_id}`}
                      className="flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-xs text-slate-600 w-4 shrink-0">
                          {i + 1}.
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm text-slate-200 truncate group-hover:text-gold-400 transition-colors">
                            {l.company_name}
                          </p>
                          <p className="text-xs text-slate-500">{l.ticker}</p>
                        </div>
                      </div>
                      <div className="text-right shrink-0 ml-2">
                        <p className="text-sm text-slate-300">
                          {formatPrice(l.price)}
                        </p>
                        <span className="text-xs font-semibold text-red-400">
                          {l.change_pct.toFixed(2)}%
                        </span>
                      </div>
                    </Link>
                  </li>
                ))}
                {data.losers.length === 0 && (
                  <li className="text-sm text-slate-500 text-center py-4">
                    No data available
                  </li>
                )}
              </ul>
            </div>
          </div>
        </section>

        {/* ============================================================= */}
        {/*  Financing Activity + News Volume                              */}
        {/* ============================================================= */}
        <section>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Financing Activity */}
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Financing Activity
                <span className="text-slate-600 normal-case ml-1">(30d)</span>
              </h2>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-3xl font-bold text-gold-400">
                    {data.financing.count_30d}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">deals closed</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-slate-100">
                    {formatUSD(data.financing.total_usd_30d)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">total raised</p>
                </div>
              </div>
            </div>

            {/* News Volume */}
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                News Volume
                <span className="text-slate-600 normal-case ml-1">(7d)</span>
              </h2>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-3xl font-bold text-gold-400">
                    {data.news.press_releases_7d}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">press releases</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-slate-100">
                    {data.news.articles_7d}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">articles</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================= */}
        {/*  Footer / Last Updated                                         */}
        {/* ============================================================= */}
        <footer className="pt-4 pb-8 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-600">
            Last updated:{" "}
            {new Date(data.timestamp).toLocaleString("en-US", {
              dateStyle: "medium",
              timeStyle: "short",
            })}
            <span className="mx-2 text-slate-700">|</span>
            Auto-refreshes every 5 minutes
          </p>
        </footer>
      </div>
    </div>
  );
}
