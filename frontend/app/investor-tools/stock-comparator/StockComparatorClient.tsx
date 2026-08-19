"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import ExportButton from "@/components/ui/ExportButton";
import { Button } from "@/components/ui/Button";
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
  close: number;
  pct: number;
}

interface Series {
  company_id: number;
  company_name: string;
  ticker: string;
  currency: string;
  points: SeriesPoint[];
}

interface SummaryRow {
  company_id: number;
  company_name: string;
  ticker: string;
  currency?: string;
  start_date?: string;
  start_price?: number;
  end_date?: string;
  end_price?: number;
  pct_change?: number;
  daily_volatility_pct?: number | null;
  data_points?: number;
  error?: string;
}

interface ComparisonData {
  available_companies: AvailableCompany[];
  series: Series[];
  summary: SummaryRow[];
  days: number;
}

/* ---------- constants ---------- */

const DAYS_OPTIONS = [
  { label: "1M", value: 30 },
  { label: "3M", value: 90 },
  { label: "6M", value: 180 },
  { label: "1Y", value: 365 },
] as const;

const MAX_COMPANIES = 10;

// Distinct line colors, assigned in series order.
const COLORS = [
  "#d4af37",
  "#38bdf8",
  "#34d399",
  "#f87171",
  "#a78bfa",
  "#fb923c",
  "#22d3ee",
  "#a3e635",
  "#e879f9",
  "#f472b6",
];

/* ---------- helpers ---------- */

function fmtPct(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function pctColor(value: number | null | undefined): string {
  if (value == null) return "text-slate-400";
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-red-400";
  return "text-slate-300";
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });
}

/* ---------- normalized performance chart (custom SVG) ---------- */

function PerformanceChart({
  series,
  colorOf,
}: {
  series: Series[];
  colorOf: (id: number) => string;
}) {
  const W = 900;
  const H = 360;
  const padL = 54;
  const padR = 20;
  const padT = 20;
  const padB = 38;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const allPoints = series.flatMap((s) => s.points);
  if (allPoints.length === 0) return null;

  const times = allPoints.map((p) => new Date(p.date).getTime());
  const tMin = Math.min(...times);
  const tMax = Math.max(...times);

  const pcts = allPoints.map((p) => p.pct);
  let pMin = Math.min(0, ...pcts);
  let pMax = Math.max(0, ...pcts);
  if (pMin === pMax) {
    pMin -= 1;
    pMax += 1;
  }
  const margin = (pMax - pMin) * 0.08;
  pMin -= margin;
  pMax += margin;

  const xOf = (date: string) =>
    padL +
    (tMax === tMin ? 0.5 : (new Date(date).getTime() - tMin) / (tMax - tMin)) *
      plotW;
  const yOf = (pct: number) =>
    padT + (1 - (pct - pMin) / (pMax - pMin)) * plotH;

  const TICKS = 5;
  const tickValues = Array.from(
    { length: TICKS },
    (_, i) => pMin + ((pMax - pMin) * i) / (TICKS - 1),
  );

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="Normalized stock performance comparison chart"
    >
      {/* horizontal gridlines + y-axis % labels */}
      {tickValues.map((v, i) => {
        const y = yOf(v);
        const isZero = Math.abs(v) < 0.001;
        return (
          <g key={i}>
            <line
              x1={padL}
              x2={W - padR}
              y1={y}
              y2={y}
              stroke={isZero ? "#64748b" : "#1e293b"}
              strokeWidth={isZero ? 1.5 : 1}
              strokeDasharray={isZero ? "none" : "3 3"}
            />
            <text
              x={padL - 8}
              y={y + 3}
              textAnchor="end"
              className="fill-slate-500"
              fontSize="11"
            >
              {v > 0 ? "+" : ""}
              {v.toFixed(0)}%
            </text>
          </g>
        );
      })}

      {/* x-axis date labels (start / end) */}
      <text
        x={padL}
        y={H - 12}
        textAnchor="start"
        className="fill-slate-500"
        fontSize="11"
      >
        {fmtDate(new Date(tMin).toISOString())}
      </text>
      <text
        x={W - padR}
        y={H - 12}
        textAnchor="end"
        className="fill-slate-500"
        fontSize="11"
      >
        {fmtDate(new Date(tMax).toISOString())}
      </text>

      {/* one polyline per company */}
      {series.map((s) => {
        const pts = s.points
          .map((p) => `${xOf(p.date).toFixed(1)},${yOf(p.pct).toFixed(1)}`)
          .join(" ");
        const last = s.points[s.points.length - 1];
        return (
          <g key={s.company_id}>
            <polyline
              points={pts}
              fill="none"
              stroke={colorOf(s.company_id)}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {last && (
              <circle
                cx={xOf(last.date)}
                cy={yOf(last.pct)}
                r={3}
                fill={colorOf(s.company_id)}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}

/* ---------- page ---------- */

export default function StockComparatorClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [selected, setSelected] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [days, setDays] = useState<number>(90);

  const [data, setData] = useState<ComparisonData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the available-companies list once for the picker.
  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.stockComparison({})) as ComparisonData;
        setAvailable(res.available_companies || []);
      } catch {
        setError("Failed to load the company list. Please refresh.");
      } finally {
        setInitialLoading(false);
      }
    })();
  }, []);

  const selectedIds = useMemo(
    () => new Set(selected.map((c) => c.id)),
    [selected],
  );

  const searchMatches = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return available
      .filter(
        (c) =>
          !selectedIds.has(c.id) &&
          (c.name.toLowerCase().includes(q) ||
            (c.ticker || "").toLowerCase().includes(q)),
      )
      .slice(0, 8);
  }, [search, available, selectedIds]);

  const addCompany = (c: AvailableCompany) => {
    if (selectedIds.has(c.id) || selected.length >= MAX_COMPANIES) return;
    setSelected((prev) => [...prev, c]);
    setSearch("");
  };

  const removeCompany = (id: number) => {
    setSelected((prev) => prev.filter((c) => c.id !== id));
  };

  const runComparison = useCallback(async () => {
    if (selected.length < 1) {
      setError("Add at least one company to compare.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = (await toolsAPI.stockComparison({
        company_ids: selected.map((c) => c.id).join(","),
        days: String(days),
      })) as ComparisonData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to run the comparison.");
    } finally {
      setLoading(false);
    }
  }, [selected, days]);

  // Stable color per company, assigned in series order.
  const colorOf = useMemo(() => {
    const order = (data?.series || []).map((s) => s.company_id);
    return (id: number) =>
      COLORS[Math.max(0, order.indexOf(id)) % COLORS.length];
  }, [data]);

  return (
    <>

      {/* Builder */}
      <section className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-5 sm:p-6 space-y-5">
            {/* Company picker */}
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2">
                Companies ({selected.length}/{MAX_COMPANIES})
              </label>

              {/* selected chips */}
              {selected.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {selected.map((c) => (
                    <span
                      key={c.id}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/30 text-sm text-gold-300"
                    >
                      {c.ticker || c.name}
                      <button
                        onClick={() => removeCompany(c.id)}
                        className="text-gold-400/70 hover:text-gold-200"
                        aria-label={`Remove ${c.name}`}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {/* search input */}
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={
                    initialLoading
                      ? "Loading companies…"
                      : selected.length >= MAX_COMPANIES
                        ? "Maximum of 10 companies reached"
                        : "Search a company by name or ticker…"
                  }
                  disabled={initialLoading || selected.length >= MAX_COMPANIES}
                  className="w-full bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-3 py-2 focus:border-gold-500/50 focus:outline-none disabled:opacity-50"
                />
                {searchMatches.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-slate-800 border border-slate-700 rounded-md shadow-xl max-h-64 overflow-y-auto">
                    {searchMatches.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => addCompany(c)}
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
            </div>

            {/* Window + run */}
            <div className="flex flex-wrap items-center justify-between gap-3">
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
              <Button
                variant="primary"
                onClick={runComparison}
                disabled={loading || selected.length < 1}
              >
                {loading ? "Comparing…" : "Compare"}
              </Button>
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto space-y-8">
          {!data && !loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Add companies above and hit{" "}
              <span className="text-gold-400">Compare</span> to see their
              normalized performance.
            </div>
          )}

          {data && data.series.length > 0 && (
            <>
              {/* Chart */}
              <div className="glass-card rounded-xl p-6">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  Normalized Performance — last {data.days} days
                </h2>
                <PerformanceChart series={data.series} colorOf={colorOf} />
                {/* Legend */}
                <div className="flex flex-wrap gap-4 mt-4">
                  {data.series.map((s) => (
                    <div
                      key={s.company_id}
                      className="flex items-center gap-2 text-sm"
                    >
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: colorOf(s.company_id) }}
                      />
                      <span className="text-slate-300">
                        {s.ticker || s.company_name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ranking table */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-sm font-semibold text-gold-400">
                    Performance Ranking
                  </h2>
                  <ExportButton
                    filename="stock-comparison"
                    rows={data.summary}
                    columns={[
                      { label: "Company", value: (r) => r.company_name },
                      { label: "Ticker", value: (r) => r.ticker },
                      { label: "Currency", value: (r) => r.currency },
                      { label: "Start date", value: (r) => r.start_date },
                      { label: "Start price", value: (r) => r.start_price },
                      { label: "End date", value: (r) => r.end_date },
                      { label: "End price", value: (r) => r.end_price },
                      { label: "Change %", value: (r) => r.pct_change },
                      {
                        label: "Daily volatility %",
                        value: (r) => r.daily_volatility_pct,
                      },
                      { label: "Data points", value: (r) => r.data_points },
                    ]}
                  />
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                        <th className="text-left pb-2 pr-4">#</th>
                        <th className="text-left pb-2 pr-4">Company</th>
                        <th className="text-left pb-2 pr-4">Ticker</th>
                        <th className="text-right pb-2 pr-4">Start</th>
                        <th className="text-right pb-2 pr-4">End</th>
                        <th className="text-right pb-2 pr-4">% Change</th>
                        <th className="text-right pb-2">Daily Vol.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.summary.map((row, i) => (
                        <tr
                          key={row.company_id}
                          className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="py-2 pr-4 text-slate-500">{i + 1}</td>
                          <td className="py-2 pr-4">
                            <Link
                              href={`/companies/${row.company_id}`}
                              className="text-slate-200 hover:text-gold-400 transition-colors"
                            >
                              {row.company_name}
                            </Link>
                          </td>
                          <td className="py-2 pr-4">
                            <Badge variant="slate">{row.ticker || "—"}</Badge>
                          </td>
                          {row.error ? (
                            <td
                              colSpan={4}
                              className="py-2 text-right text-slate-500 italic"
                            >
                              {row.error}
                            </td>
                          ) : (
                            <>
                              <td className="py-2 pr-4 text-right text-slate-400">
                                {row.start_price?.toFixed(3)}{" "}
                                <span className="text-slate-600">
                                  {row.currency}
                                </span>
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-300">
                                {row.end_price?.toFixed(3)}{" "}
                                <span className="text-slate-600">
                                  {row.currency}
                                </span>
                              </td>
                              <td
                                className={`py-2 pr-4 text-right font-semibold ${pctColor(
                                  row.pct_change,
                                )}`}
                              >
                                {fmtPct(row.pct_change)}
                              </td>
                              <td className="py-2 text-right text-slate-400">
                                {row.daily_volatility_pct != null
                                  ? `${row.daily_volatility_pct.toFixed(2)}%`
                                  : "—"}
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  % Change is the move from the first to the last trading day in
                  the window. Daily Vol. is the standard deviation of daily
                  returns — higher means a choppier ride.
                </p>
              </div>
            </>
          )}

          {data && data.series.length === 0 && !loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              None of the selected companies have enough price history in this
              window. Try a longer window or different companies.
            </div>
          )}
        </div>
      </section>
    </>
  );
}
