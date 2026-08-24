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
  median_daily_dollar_volume: number;
  sessions_sampled: number;
  tradeable_per_day: number;
  days_to_exit: number | null;
  band: string;
  market_cap_usd: number | null;
  current_price: number | null;
}

interface Data {
  results: Row[];
  count: number;
  distribution: Record<string, number>;
  summary: {
    companies: number;
    median_daily_dollar_volume: number;
    under_5k: number;
    position_size: number;
    participation_rate: number;
  };
  assumptions: { lookback_sessions: number; method: string; currency: string };
  bands: string[];
}

const BAND_LABEL: Record<string, string> = {
  untradeable: "Untradeable",
  very_thin: "Very thin",
  thin: "Thin",
  moderate: "Moderate",
  liquid: "Liquid",
};

const BAND_STYLE: Record<string, string> = {
  untradeable: "text-red-300 border-red-500/40 bg-red-500/10",
  very_thin: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  thin: "text-yellow-200 border-yellow-500/30 bg-yellow-500/10",
  moderate: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
  liquid: "text-emerald-200 border-emerald-400/50 bg-emerald-400/10",
};

function money(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return `$${Math.round(v).toLocaleString()}`;
}

function exitLabel(days: number | null): string {
  if (days === null) return "—";
  if (days < 1) return "same day";
  if (days > 250) return `${(days / 250).toFixed(1)} yrs`;
  return `${days.toFixed(days < 10 ? 1 : 0)} days`;
}

export default function LiquidityScreenerClient() {
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [position, setPosition] = useState("25000");
  const [band, setBand] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    toolsAPI
      .liquidityScreener({ position, ...(band ? { band } : {}) })
      .then((d) => !cancelled && setData(d))
      .catch(
        (e) =>
          !cancelled &&
          setError(e?.message || "Could not load liquidity data."),
      )
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [position, band]);

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

  const pctThin = data
    ? Math.round(
        (data.summary.under_5k / Math.max(1, data.summary.companies)) * 100,
      )
    : 0;

  return (
    <>

      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto">
          {loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Measuring order books…
            </div>
          )}

          {error && !loading && (
            <div className="glass-card rounded-xl p-6 border-red-500/30">
              <p className="text-red-300 font-medium mb-1">
                Could not load liquidity data
              </p>
              <p className="text-sm text-slate-400">{error}</p>
            </div>
          )}

          {data && !loading && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Companies measured
                  </div>
                  <div className="text-xl font-semibold text-slate-200 tabular-nums">
                    {data.summary.companies}
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Median daily volume
                  </div>
                  <div className="text-xl font-semibold text-slate-200 tabular-nums">
                    {money(data.summary.median_daily_dollar_volume)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    across the sector
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Under $5K a day
                  </div>
                  <div className="text-xl font-semibold text-red-300 tabular-nums">
                    {pctThin}%
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {data.summary.under_5k} companies
                  </div>
                </div>
                <div className="glass-card rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                    Sessions sampled
                  </div>
                  <div className="text-xl font-semibold text-slate-200 tabular-nums">
                    {data.assumptions.lookback_sessions}
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-xl p-4 mb-6 flex flex-wrap items-end gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Position size
                  </label>
                  <select
                    value={position}
                    onChange={(e) => setPosition(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
                  >
                    {[
                      "5000",
                      "10000",
                      "25000",
                      "50000",
                      "100000",
                      "250000",
                    ].map((v) => (
                      <option key={v} value={v}>
                        ${Number(v).toLocaleString()}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Liquidity band
                  </label>
                  <select
                    value={band}
                    onChange={(e) => setBand(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
                  >
                    <option value="">All bands</option>
                    {data.bands.map((b) => (
                      <option key={b} value={b}>
                        {BAND_LABEL[b] ?? b}
                      </option>
                    ))}
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
                  filename="liquidity-screener"
                  rows={rows}
                  columns={[
                    { label: "Company", value: (r) => r.company_name },
                    { label: "Ticker", value: (r) => r.ticker },
                    { label: "Exchange", value: (r) => r.exchange },
                    { label: "Price", value: (r) => r.current_price },
                    {
                      label: "Median daily $ volume",
                      value: (r) => r.median_daily_dollar_volume,
                    },
                    {
                      label: "Tradeable per day",
                      value: (r) => r.tradeable_per_day,
                    },
                    { label: "Days to exit", value: (r) => r.days_to_exit },
                    { label: "Band", value: (r) => r.band },
                    { label: "Sessions", value: (r) => r.sessions_sampled },
                    { label: "Market cap USD", value: (r) => r.market_cap_usd },
                  ]}
                />
              </div>

              {rows.length === 0 ? (
                <EmptyState
                  title="No companies match"
                  detail="Try a different liquidity band or clear the search. Companies with fewer than five traded sessions in the sample window are excluded, since a median from that little data would be noise."
                />
              ) : (
                <div className="glass-card rounded-xl overflow-hidden">
                  {/* These tables are wider than a phone; say so rather than leaving the overflow to be discovered. */}
                  <p className="lg:hidden px-4 pt-3 text-xs text-slate-500">Swipe the table sideways to see all columns.</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[720px]">
                      <thead>
                        <tr className="border-b border-slate-700/60 text-[11px] uppercase tracking-wider text-slate-500">
                          <th className="text-left px-4 py-3">Company</th>
                          <th className="text-right px-3 py-3">Price</th>
                          <th className="text-right px-3 py-3">
                            Median daily volume
                          </th>
                          <th className="text-right px-3 py-3">
                            Sellable per day
                          </th>
                          <th className="text-right px-3 py-3">
                            Days to exit {money(data.summary.position_size)}
                          </th>
                          <th className="text-right px-4 py-3">Liquidity</th>
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
                                {r.exchange
                                  ? ` · ${r.exchange.toUpperCase()}`
                                  : ""}
                              </div>
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                              {r.current_price === null
                                ? "—"
                                : `$${r.current_price.toFixed(3)}`}
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                              {money(r.median_daily_dollar_volume)}
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums text-slate-400">
                              {money(r.tradeable_per_day)}
                            </td>
                            <td className="px-3 py-3 text-right tabular-nums">
                              <span
                                className={
                                  r.days_to_exit !== null && r.days_to_exit > 20
                                    ? "text-red-300"
                                    : "text-slate-200"
                                }
                              >
                                {exitLabel(r.days_to_exit)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <span
                                className={`inline-block text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${BAND_STYLE[r.band] ?? ""}`}
                              >
                                {BAND_LABEL[r.band] ?? r.band}
                              </span>
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
                  How this is measured
                </h3>
                <ul className="text-xs text-slate-400 space-y-2 leading-relaxed">
                  <li>{data.assumptions.method}</li>
                  <li>{data.assumptions.currency}</li>
                  <li>
                    Companies whose price data has gone stale are excluded
                    entirely — a large median from bars months old describes a
                    stock that no longer trades, not a liquid one.
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
