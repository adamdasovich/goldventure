"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Badge } from "@/components/ui/Badge";
import CompanyActions from "@/components/ui/CompanyActions";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
}

interface SeriesPoint {
  date: string;
  volume: number;
  trailing_avg_volume: number;
  volume_ratio: number;
  price_change_pct: number;
  flagged: boolean;
}

interface RelatedNews {
  title: string;
  date: string;
  type: string;
  url: string;
}

interface FlaggedDay {
  date: string;
  volume: number;
  trailing_avg_volume: number;
  volume_ratio: number;
  price_change_pct: number;
  explained: boolean;
  related_news: RelatedNews[];
}

interface ActivityData {
  available_companies: AvailableCompany[];
  company?: { id: number; name: string; ticker: string };
  window_days: number;
  volume_multiple: number;
  series: SeriesPoint[];
  flagged_days: FlaggedDay[];
  summary?: {
    trading_days: number;
    unusual_days: number;
    unexplained_days: number;
  };
  message?: string;
}

/* ---------- constants ---------- */

const DAYS_OPTIONS = [
  { label: "1M", value: 30 },
  { label: "3M", value: 90 },
  { label: "6M", value: 180 },
  { label: "1Y", value: 365 },
] as const;

const MULTIPLE_OPTIONS = [2, 2.5, 3, 4] as const;

/* ---------- helpers ---------- */

function fmtVol(v: number | null | undefined): string {
  if (!v) return "0";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return Math.round(v).toLocaleString();
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function pctColor(value: number): string {
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-red-400";
  return "text-slate-300";
}

/* ---------- page ---------- */

export default function UnusualActivityClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AvailableCompany | null>(null);
  const [days, setDays] = useState<number>(90);
  const [multiple, setMultiple] = useState<number>(2.5);
  const [data, setData] = useState<ActivityData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the available-companies list once for the picker.
  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.unusualActivity({})) as ActivityData;
        setAvailable(res.available_companies || []);
      } catch {
        setError("Failed to load the company list. Please refresh.");
      } finally {
        setInitialLoading(false);
      }
    })();
  }, []);

  const searchMatches = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return available
      .filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.ticker || "").toLowerCase().includes(q),
      )
      .slice(0, 8);
  }, [search, available]);

  // Adopt ?company_id= so links from other tools land on the right company
  // instead of an empty picker. Read off window.location rather than
  // useSearchParams, which would force this prerendered page's client tree
  // into a Suspense boundary just to satisfy the build.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const requested = new URLSearchParams(window.location.search).get(
      "company_id",
    );
    if (!requested || selected || available.length === 0) return;
    const match = available.find((c) => String(c.id) === requested);
    if (match) setSelected(match);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [available, selected]);


  const runScan = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const res = (await toolsAPI.unusualActivity({
        company_id: String(selected.id),
        days: String(days),
        volume_multiple: String(multiple),
      })) as ActivityData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to scan for unusual activity.");
    } finally {
      setLoading(false);
    }
  }, [selected, days, multiple]);

  // Re-scan whenever the company or filters change.
  useEffect(() => {
    if (selected) runScan();
  }, [selected, days, multiple, runScan]);

  const maxVolume = useMemo(() => {
    if (!data?.series?.length) return 1;
    return Math.max(...data.series.map((s) => s.volume), 1);
  }, [data]);

  return (
    <>

      {/* Controls */}
      <section className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-5 sm:p-6 space-y-5">
            {/* Company picker */}
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2">
                Company
              </label>
              {selected ? (
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/30 text-sm text-gold-300">
                    {selected.name}
                    {selected.ticker && (
                      <span className="text-gold-400/60">
                        {selected.ticker}
                      </span>
                    )}
                  </span>
                  <button
                    onClick={() => {
                      setSelected(null);
                      setData(null);
                    }}
                    className="text-sm text-slate-400 hover:text-gold-400"
                  >
                    Change
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder={
                      initialLoading
                        ? "Loading companies…"
                        : "Search a company by name or ticker…"
                    }
                    disabled={initialLoading}
                    className="w-full bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-3 py-2 focus:border-gold-500/50 focus:outline-none disabled:opacity-50"
                  />
                  {searchMatches.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full bg-slate-800 border border-slate-700 rounded-md shadow-xl max-h-64 overflow-y-auto">
                      {searchMatches.map((c) => (
                        <button
                          key={c.id}
                          onClick={() => {
                            setSelected(c);
                            setSearch("");
                          }}
                          className="block w-full text-left px-3 py-2 text-sm hover:bg-slate-700/60 transition-colors"
                        >
                          <span className="text-slate-200">{c.name}</span>
                          {c.ticker && (
                            <span className="text-slate-500 ml-2">
                              {c.ticker}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {selected && (
              <div className="border-t border-slate-700/40 pt-3">
                <CompanyActions
                  companyId={selected.id}
                  companyName={selected.name}
                  currentSlug="unusual-activity"
                />
              </div>
            )}

            {/* Window + threshold */}
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-400 mr-1">Window:</span>
                {DAYS_OPTIONS.map((d) => (
                  <button
                    key={d.value}
                    onClick={() => setDays(d.value)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      days === d.value
                        ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                        : "bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:text-slate-200"
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-400 mr-1">
                  Spike threshold:
                </span>
                {MULTIPLE_OPTIONS.map((m) => (
                  <button
                    key={m}
                    onClick={() => setMultiple(m)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      multiple === m
                        ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                        : "bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:text-slate-200"
                    }`}
                  >
                    {m}×
                  </button>
                ))}
              </div>
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto space-y-8">
          {!selected && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Search and select a company above to scan for unusual trading
              volume.
            </div>
          )}

          {selected && loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Scanning trading history…
            </div>
          )}

          {selected && !loading && data && data.message && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              {data.message}
            </div>
          )}

          {selected && !loading && data && !data.message && data.summary && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Trading Days
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {data.summary.trading_days}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    scanned in window
                  </p>
                </div>
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Unusual Days
                  </p>
                  <p className="text-2xl font-bold text-gold-400">
                    {data.summary.unusual_days}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    volume ≥ {data.volume_multiple}× average
                  </p>
                </div>
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Unexplained
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {data.summary.unexplained_days}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    no news within ±2 days
                  </p>
                </div>
              </div>

              {/* Volume chart */}
              {data.series.length > 0 && (
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-1">
                    Daily Volume
                  </h2>
                  <p className="text-xs text-slate-500 mb-4">
                    Gold bars are unusual-volume days; grey bars are normal
                    trading.
                  </p>
                  <div className="flex items-end gap-[2px] h-48">
                    {data.series.map((s) => {
                      const pct = (s.volume / maxVolume) * 100;
                      return (
                        <div
                          key={s.date}
                          className="flex-1 min-w-0 flex items-end"
                          style={{ height: "100%" }}
                        >
                          <div
                            className={`w-full rounded-t transition-all ${
                              s.flagged
                                ? "bg-gradient-to-t from-gold-600 to-gold-400"
                                : "bg-slate-700/70"
                            }`}
                            style={{ height: `${Math.max(pct, 1)}%` }}
                            title={`${fmtDate(s.date)} — ${fmtVol(
                              s.volume,
                            )} vol (${s.volume_ratio}× avg)${
                              s.flagged ? " — UNUSUAL" : ""
                            }`}
                          />
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 mt-2">
                    <span>{fmtDate(data.series[0].date)}</span>
                    <span>
                      {fmtDate(data.series[data.series.length - 1].date)}
                    </span>
                  </div>
                </div>
              )}

              {/* Flagged days table */}
              {data.flagged_days.length > 0 ? (
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-4">
                    Unusual-Volume Days (highest spike first)
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                          <th className="text-left pb-2 pr-4">Date</th>
                          <th className="text-right pb-2 pr-4">Volume</th>
                          <th className="text-right pb-2 pr-4">vs Avg</th>
                          <th className="text-right pb-2 pr-4">Price Move</th>
                          <th className="text-left pb-2">
                            News Context (±2 days)
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.flagged_days.map((d) => (
                          <tr
                            key={d.date}
                            className="border-b border-slate-800/40 align-top"
                          >
                            <td className="py-2.5 pr-4 text-slate-300 whitespace-nowrap">
                              {fmtDate(d.date)}
                            </td>
                            <td className="py-2.5 pr-4 text-right text-slate-300">
                              {fmtVol(d.volume)}
                            </td>
                            <td className="py-2.5 pr-4 text-right font-semibold text-gold-400">
                              {d.volume_ratio}×
                            </td>
                            <td
                              className={`py-2.5 pr-4 text-right ${pctColor(
                                d.price_change_pct,
                              )}`}
                            >
                              {d.price_change_pct > 0 ? "+" : ""}
                              {d.price_change_pct.toFixed(2)}%
                            </td>
                            <td className="py-2.5">
                              {d.explained ? (
                                <div className="space-y-1">
                                  {d.related_news.map((n, i) => (
                                    <div key={i} className="text-xs">
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
                                        <span className="text-slate-300">
                                          {n.title}
                                        </span>
                                      )}
                                      <span className="text-slate-600 ml-1">
                                        ({n.type})
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <Badge variant="warning">Unexplained</Badge>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-slate-500 mt-3">
                    &quot;vs Avg&quot; compares the day&apos;s volume to the
                    trailing 20-trading-day average. Unexplained spikes — no
                    press release within ±2 days — can signal accumulation,
                    information leaks, or a sector-wide move.
                  </p>
                </div>
              ) : (
                <div className="glass-card rounded-xl p-8 text-center text-slate-400">
                  No volume spikes of {data.volume_multiple}× or more in this
                  window. Try a lower threshold or a longer window.
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
}
