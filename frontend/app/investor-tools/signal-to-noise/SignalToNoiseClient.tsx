"use client";

import { useEffect, useMemo, useState } from "react";
import ExportButton from "@/components/ui/ExportButton";
import EmptyState from "@/components/ui/EmptyState";
import { toolsAPI } from "@/lib/api";

interface Row {
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  total_releases: number;
  hard_releases: number;
  drill_releases: number;
  financing_releases: number;
  signal_pct: number;
  financing_pct: number;
}

interface Data {
  results: Row[];
  count: number;
  summary: {
    companies: number;
    sector_signal_pct: number;
    total_releases: number;
    hard_releases: number;
    min_releases: number;
    months: number;
  };
  assumptions: { hard_news_types: string[]; method: string; caveat: string };
}

export default function SignalToNoiseClient() {
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minReleases, setMinReleases] = useState("10");
  const [months, setMonths] = useState("0");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    toolsAPI
      .signalToNoise({ min_releases: minReleases, months })
      .then((d) => !cancelled && setData(d))
      .catch(
        (e) =>
          !cancelled && setError(e?.message || "Could not load news data."),
      )
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [minReleases, months]);

  const rows = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    if (!q) return data.results;
    return data.results.filter(
      (r) =>
        r.company_name.toLowerCase().includes(q) ||
        (r.ticker || "").toLowerCase().includes(q),
    );
  }, [data, search]);

  const sector = data?.summary.sector_signal_pct ?? 0;

  return (
    <>

      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto">
          {loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Reading the news archive…
            </div>
          )}

          {error && !loading && (
            <div className="glass-card rounded-xl p-6 border-red-500/30">
              <p className="text-red-300 font-medium mb-1">
                Could not load news data
              </p>
              <p className="text-sm text-slate-400">{error}</p>
            </div>
          )}

          {data && !loading && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Sector signal
                  </div>
                  <div className="text-xl font-semibold text-amber-300 tabular-nums">
                    {sector}%
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    of all releases are results
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Companies ranked
                  </div>
                  <div className="text-xl font-semibold text-slate-200 tabular-nums">
                    {data.summary.companies}
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Releases analyzed
                  </div>
                  <div className="text-xl font-semibold text-slate-200 tabular-nums">
                    {data.summary.total_releases.toLocaleString()}
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Hard results
                  </div>
                  <div className="text-xl font-semibold text-emerald-300 tabular-nums">
                    {data.summary.hard_releases.toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-xl p-4 mb-6 flex flex-wrap items-end gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Minimum releases
                  </label>
                  <select
                    value={minReleases}
                    onChange={(e) => setMinReleases(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
                  >
                    {["5", "10", "20", "50"].map((v) => (
                      <option key={v} value={v}>
                        {v}+
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Window
                  </label>
                  <select
                    value={months}
                    onChange={(e) => setMonths(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
                  >
                    <option value="0">All history</option>
                    <option value="12">Last 12 months</option>
                    <option value="24">Last 24 months</option>
                  </select>
                </div>
                <div className="flex-1 min-w-[180px]">
                  <label className="block text-xs text-slate-400 mb-1">
                    Search
                  </label>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Company or ticker"
                    className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-gold-500/50"
                  />
                </div>
                <ExportButton
                  filename="signal-to-noise"
                  rows={rows}
                  columns={[
                    { label: "Company", value: (r) => r.company_name },
                    { label: "Ticker", value: (r) => r.ticker },
                    { label: "Exchange", value: (r) => r.exchange },
                    { label: "Signal %", value: (r) => r.signal_pct },
                    { label: "Total releases", value: (r) => r.total_releases },
                    { label: "Hard results", value: (r) => r.hard_releases },
                    { label: "Drill results", value: (r) => r.drill_releases },
                    {
                      label: "Financing releases",
                      value: (r) => r.financing_releases,
                    },
                    { label: "Financing %", value: (r) => r.financing_pct },
                  ]}
                />
              </div>

              {rows.length === 0 ? (
                <EmptyState
                  title="No companies match"
                  detail="Lower the minimum-releases threshold or widen the window. Companies below the threshold are excluded because a ratio from a handful of releases says more about the sample than the company."
                />
              ) : (
                <div className="glass-card rounded-xl overflow-hidden">
                  {/* These tables are wider than a phone; say so rather than leaving the overflow to be discovered. */}
                  <p className="lg:hidden px-4 pt-3 text-xs text-slate-500">Swipe the table sideways to see all columns.</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[700px]">
                      <thead>
                        <tr className="border-b border-slate-700/60 text-[11px] uppercase tracking-wider text-slate-500">
                          <th className="text-left px-4 py-3">Company</th>
                          <th className="text-left px-3 py-3 w-56">
                            Signal vs noise
                          </th>
                          <th className="text-right px-3 py-3">Signal</th>
                          <th className="text-right px-3 py-3">Results</th>
                          <th className="text-right px-3 py-3">Drill</th>
                          <th className="text-right px-4 py-3">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r) => (
                          <tr
                            key={r.company_id}
                            className="border-b border-slate-800/60 hover:bg-slate-800/30"
                          >
                            <td className="px-4 py-3">
                              <div className="font-medium text-slate-200">
                                {r.company_name}
                              </div>
                              <div className="text-xs text-slate-500">
                                {r.ticker}
                              </div>
                            </td>
                            <td className="px-3 py-3">
                              <div
                                className="h-2 w-full rounded bg-slate-800 overflow-hidden"
                                title={`${r.signal_pct}% results, ${(100 - r.signal_pct).toFixed(1)}% other`}
                              >
                                <div
                                  className={
                                    r.signal_pct >= sector
                                      ? "h-full bg-emerald-500/70"
                                      : "h-full bg-amber-500/60"
                                  }
                                  style={{ width: `${r.signal_pct}%` }}
                                />
                              </div>
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums">
                              <span
                                className={
                                  r.signal_pct >= sector
                                    ? "text-emerald-300"
                                    : "text-slate-400"
                                }
                              >
                                {r.signal_pct.toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                              {r.hard_releases}
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums text-slate-400">
                              {r.drill_releases}
                            </td>
                            <td className="px-4 py-3 text-right tabular-nums text-slate-400">
                              {r.total_releases}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="mt-6 glass-card rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">
                  How to read this
                </h3>
                <ul className="text-xs text-slate-400 space-y-2 leading-relaxed">
                  <li>{data.assumptions.method}</li>
                  <li>{data.assumptions.caveat}</li>
                  <li>
                    The bar is shaded green when a company beats the sector
                    average of {sector}% and amber when it does not.
                  </li>
                </ul>
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}
