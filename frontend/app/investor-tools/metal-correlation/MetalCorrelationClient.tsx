"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Badge } from "@/components/ui/Badge";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
  suggested_metal: string | null;
}

interface AvailableMetal {
  symbol: string;
  name: string;
}

interface SeriesPoint {
  date: string;
  pct: number;
  close?: number;
  price?: number;
}

interface CompanyResult {
  company_id: number;
  company_name: string;
  ticker: string;
  currency?: string;
  stock_series?: SeriesPoint[];
  start_date?: string;
  end_date?: string;
  start_price?: number;
  end_price?: number;
  stock_pct_change?: number;
  correlation: number | null;
  r_squared: number | null;
  beta: number | null;
  stock_volatility_pct: number | null;
  metal_volatility_pct: number | null;
  leverage_ratio: number | null;
  t_stat: number | null;
  significant: boolean;
  data_points: number;
  error?: string;
}

interface MetalMeta {
  symbol: string;
  name: string;
  unit: string;
  pct_change: number | null;
  volatility_pct: number | null;
}

interface HeatmapData {
  labels: string[];
  matrix: (number | null)[][];
}

interface ToolData {
  available_companies: AvailableCompany[];
  available_metals: AvailableMetal[];
  metal?: MetalMeta;
  metal_series: SeriesPoint[];
  companies: CompanyResult[];
  heatmap?: HeatmapData;
  days: number;
  message?: string;
}

/* ---------- constants ---------- */

const DAYS_OPTIONS = [
  { label: "3M", value: 90 },
  { label: "6M", value: 180 },
  { label: "1Y", value: 365 },
  { label: "2Y", value: 730 },
] as const;

const MAX_COMPANIES = 10;

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
const METAL_COLOR = "#facc15"; // amber — distinguished from stock palette

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

// Map a correlation in [-1, 1] to a red-white-green cell color for the heatmap.
function corrColor(r: number | null): string {
  if (r == null) return "#1e293b";
  const c = Math.max(-1, Math.min(1, r));
  // -1 → red, 0 → neutral slate, +1 → green
  if (c >= 0) {
    const alpha = c.toFixed(2);
    return `rgba(52, 211, 153, ${alpha})`;
  }
  const alpha = Math.abs(c).toFixed(2);
  return `rgba(248, 113, 113, ${alpha})`;
}

function corrLabel(r: number | null): string {
  if (r == null) return "—";
  const abs = Math.abs(r);
  if (abs >= 0.7) return "Strong";
  if (abs >= 0.4) return "Moderate";
  if (abs >= 0.2) return "Weak";
  return "None";
}

function betaLabel(beta: number | null): string {
  if (beta == null) return "—";
  if (beta >= 1.5) return "High leverage";
  if (beta >= 1.0) return "Leveraged";
  if (beta >= 0.5) return "Tracks";
  if (beta >= -0.5) return "Decoupled";
  return "Inverse";
}

/* ---------- overlay chart: metal + selected stocks, normalized to 0% ---------- */

function OverlayChart({
  metalSeries,
  companies,
  metalName,
  colorOf,
}: {
  metalSeries: SeriesPoint[];
  companies: CompanyResult[];
  metalName: string;
  colorOf: (id: number) => string;
}) {
  const W = 900;
  const H = 380;
  const padL = 56;
  const padR = 24;
  const padT = 20;
  const padB = 38;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const stockSeriesArr = companies
    .filter((c) => c.stock_series && c.stock_series.length > 0)
    .map((c) => ({
      id: c.company_id,
      ticker: c.ticker || c.company_name,
      points: c.stock_series!,
    }));

  const allPoints: SeriesPoint[] = [
    ...metalSeries,
    ...stockSeriesArr.flatMap((s) => s.points),
  ];
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
      aria-label={`${metalName} price vs selected stock prices (normalized)`}
    >
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

      {/* Metal line — thicker, dashed, on top so it's always readable */}
      {metalSeries.length > 1 && (
        <polyline
          points={metalSeries
            .map((p) => `${xOf(p.date).toFixed(1)},${yOf(p.pct).toFixed(1)}`)
            .join(" ")}
          fill="none"
          stroke={METAL_COLOR}
          strokeWidth={3}
          strokeDasharray="6 4"
          strokeLinejoin="round"
          strokeLinecap="round"
          opacity={0.9}
        />
      )}

      {stockSeriesArr.map((s) => {
        const pts = s.points
          .map((p) => `${xOf(p.date).toFixed(1)},${yOf(p.pct).toFixed(1)}`)
          .join(" ");
        const last = s.points[s.points.length - 1];
        return (
          <g key={s.id}>
            <polyline
              points={pts}
              fill="none"
              stroke={colorOf(s.id)}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {last && (
              <circle
                cx={xOf(last.date)}
                cy={yOf(last.pct)}
                r={3}
                fill={colorOf(s.id)}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}

/* ---------- correlation heatmap ---------- */

function Heatmap({ data }: { data: HeatmapData }) {
  const labels = data.labels;
  const matrix = data.matrix;
  if (labels.length === 0) return null;

  const CELL = 56;
  const LABEL_PAD = 96;
  const W = LABEL_PAD + labels.length * CELL + 12;
  const H = LABEL_PAD + labels.length * CELL + 12;

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        className="block"
        role="img"
        aria-label="Pairwise correlation heatmap"
      >
        {/* column labels (rotated) */}
        {labels.map((l, i) => (
          <g
            key={`col-${i}`}
            transform={`translate(${LABEL_PAD + i * CELL + CELL / 2}, ${LABEL_PAD - 8})`}
          >
            <text
              transform="rotate(-45)"
              textAnchor="start"
              className="fill-slate-400"
              fontSize="11"
            >
              {l}
            </text>
          </g>
        ))}
        {/* row labels */}
        {labels.map((l, i) => (
          <text
            key={`row-${i}`}
            x={LABEL_PAD - 6}
            y={LABEL_PAD + i * CELL + CELL / 2 + 4}
            textAnchor="end"
            className="fill-slate-400"
            fontSize="11"
          >
            {l}
          </text>
        ))}
        {/* cells */}
        {matrix.map((row, i) =>
          row.map((v, j) => (
            <g key={`cell-${i}-${j}`}>
              <rect
                x={LABEL_PAD + j * CELL}
                y={LABEL_PAD + i * CELL}
                width={CELL - 2}
                height={CELL - 2}
                fill={corrColor(v)}
                stroke="#0f172a"
                strokeWidth={1}
                rx={3}
              />
              <text
                x={LABEL_PAD + j * CELL + CELL / 2}
                y={LABEL_PAD + i * CELL + CELL / 2 + 4}
                textAnchor="middle"
                fontSize="11"
                className={
                  v != null && Math.abs(v) > 0.5
                    ? "fill-slate-900 font-semibold"
                    : "fill-slate-300"
                }
              >
                {v == null ? "—" : v.toFixed(2)}
              </text>
            </g>
          )),
        )}
      </svg>
    </div>
  );
}

/* ---------- page ---------- */

export default function MetalCorrelationClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [metals, setMetals] = useState<AvailableMetal[]>([]);
  const [selected, setSelected] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [metal, setMetal] = useState<string>("XAU");
  const [days, setDays] = useState<number>(180);

  const [data, setData] = useState<ToolData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.metalCorrelation({})) as ToolData;
        setAvailable(res.available_companies || []);
        setMetals(res.available_metals || []);
        // Prefer gold if present, else first available metal.
        const symbols = (res.available_metals || []).map((m) => m.symbol);
        if (symbols.length && !symbols.includes("XAU")) {
          setMetal(symbols[0]);
        }
      } catch {
        setError("Failed to load picker data. Please refresh.");
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
    // If user has only this company, snap the metal to its suggested one.
    if (selected.length === 0 && c.suggested_metal) {
      const symbols = metals.map((m) => m.symbol);
      if (symbols.includes(c.suggested_metal)) setMetal(c.suggested_metal);
    }
  };

  const removeCompany = (id: number) => {
    setSelected((prev) => prev.filter((c) => c.id !== id));
  };

  const runAnalysis = useCallback(async () => {
    if (selected.length < 1) {
      setError("Add at least one company to analyze.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = (await toolsAPI.metalCorrelation({
        metal,
        company_ids: selected.map((c) => c.id).join(","),
        days: String(days),
      })) as ToolData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to run the analysis.");
    } finally {
      setLoading(false);
    }
  }, [selected, days, metal]);

  // Stable color per company across chart, legend, and table.
  const colorOf = useMemo(() => {
    const order = (data?.companies || []).map((c) => c.company_id);
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

            {/* Metal + window + run */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Metal:</span>
                  <select
                    value={metal}
                    onChange={(e) => setMetal(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-2 py-1 focus:border-gold-500/50 focus:outline-none"
                    disabled={metals.length === 0}
                  >
                    {metals.map((m) => (
                      <option key={m.symbol} value={m.symbol}>
                        {m.name} ({m.symbol})
                      </option>
                    ))}
                  </select>
                </div>

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
              </div>
              <Button
                variant="primary"
                onClick={runAnalysis}
                disabled={loading || selected.length < 1}
              >
                {loading ? "Analyzing…" : "Analyze"}
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
              Pick a metal, add companies, and hit{" "}
              <span className="text-gold-400">Analyze</span> to see how each
              stock tracks the metal.
            </div>
          )}

          {data?.message && (
            <div className="glass-card rounded-xl p-6 text-center text-slate-400">
              {data.message}
            </div>
          )}

          {data && data.metal && data.companies.length > 0 && (
            <>
              {/* Metal summary header */}
              <div className="glass-card rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider">
                    Benchmark
                  </div>
                  <div className="text-lg font-semibold text-slate-200">
                    {data.metal.name}{" "}
                    <span className="text-slate-500 text-sm">
                      ({data.metal.symbol} · USD/{data.metal.unit})
                    </span>
                  </div>
                </div>
                <div className="flex gap-6 text-sm">
                  <div>
                    <div className="text-xs text-slate-500 uppercase tracking-wider">
                      Window
                    </div>
                    <div className="text-slate-300">{data.days} days</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase tracking-wider">
                      Metal % Δ
                    </div>
                    <div className={pctColor(data.metal.pct_change)}>
                      {fmtPct(data.metal.pct_change)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase tracking-wider">
                      Metal Daily Vol.
                    </div>
                    <div className="text-slate-300">
                      {data.metal.volatility_pct != null
                        ? `${data.metal.volatility_pct.toFixed(2)}%`
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Overlay chart */}
              <div className="glass-card rounded-xl p-6">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  {data.metal.name} vs Selected Stocks — normalized to 0%
                </h2>
                <OverlayChart
                  metalSeries={data.metal_series}
                  companies={data.companies}
                  metalName={data.metal.name}
                  colorOf={colorOf}
                />
                <div className="flex flex-wrap gap-4 mt-4">
                  <div className="flex items-center gap-2 text-sm">
                    <span
                      className="inline-block w-6 border-t-2 border-dashed"
                      style={{ borderColor: METAL_COLOR }}
                    />
                    <span className="text-slate-300 font-medium">
                      {data.metal.name}
                    </span>
                  </div>
                  {data.companies
                    .filter((c) => !c.error)
                    .map((c) => (
                      <div
                        key={c.company_id}
                        className="flex items-center gap-2 text-sm"
                      >
                        <span
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: colorOf(c.company_id) }}
                        />
                        <span className="text-slate-300">
                          {c.ticker || c.company_name}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Leverage table */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-sm font-semibold text-gold-400">
                    Leverage &amp; Sensitivity Metrics
                  </h2>
                  <ExportButton
                    filename={`metal-leverage-${data.metal?.symbol ?? "metal"}`}
                    rows={data.companies}
                    columns={[
                      { label: "Company", value: (c) => c.company_name },
                      { label: "Ticker", value: (c) => c.ticker },
                      { label: "Correlation", value: (c) => c.correlation },
                      { label: "R squared", value: (c) => c.r_squared },
                      { label: "Beta", value: (c) => c.beta },
                      {
                        label: "Stock volatility %",
                        value: (c) => c.stock_volatility_pct,
                      },
                      {
                        label: "Metal volatility %",
                        value: (c) => c.metal_volatility_pct,
                      },
                      { label: "Leverage ratio", value: (c) => c.leverage_ratio },
                      { label: "t-stat", value: (c) => c.t_stat },
                      {
                        label: "Significant",
                        value: (c) => (c.significant ? "yes" : "no"),
                      },
                      { label: "Stock change %", value: (c) => c.stock_pct_change },
                      { label: "Data points", value: (c) => c.data_points },
                    ]}
                  />
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                        <th className="text-left pb-2 pr-4">Company</th>
                        <th className="text-left pb-2 pr-4">Ticker</th>
                        <th
                          className="text-right pb-2 pr-4"
                          title="Pearson correlation of daily returns. Range −1 to +1."
                        >
                          Corr (r)
                        </th>
                        <th
                          className="text-right pb-2 pr-4"
                          title="r² — the share of stock-return variance explained by the metal."
                        >
                          R²
                        </th>
                        <th
                          className="text-right pb-2 pr-4"
                          title="Beta: stock-return change per 1% metal-return change."
                        >
                          Beta
                        </th>
                        <th
                          className="text-right pb-2 pr-4"
                          title="Stock daily volatility ÷ metal daily volatility."
                        >
                          Leverage
                        </th>
                        <th className="text-right pb-2 pr-4">Stock Vol.</th>
                        <th className="text-right pb-2 pr-4">Stock % Δ</th>
                        <th
                          className="text-right pb-2"
                          title="95% confidence the correlation is non-zero (|t| ≥ 1.96)."
                        >
                          Sig.
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.companies.map((c) => (
                        <tr
                          key={c.company_id}
                          className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="py-2 pr-4">
                            <Link
                              href={`/companies/${c.company_id}`}
                              className="text-slate-200 hover:text-gold-400 transition-colors"
                            >
                              <span
                                className="inline-block w-2 h-2 rounded-full mr-2"
                                style={{
                                  backgroundColor: colorOf(c.company_id),
                                }}
                              />
                              {c.company_name}
                            </Link>
                          </td>
                          <td className="py-2 pr-4">
                            <Badge variant="slate">{c.ticker || "—"}</Badge>
                          </td>
                          {c.error ? (
                            <td
                              colSpan={7}
                              className="py-2 text-right text-slate-500 italic"
                            >
                              {c.error}
                            </td>
                          ) : (
                            <>
                              <td className="py-2 pr-4 text-right">
                                <div
                                  className={`font-semibold ${pctColor(c.correlation)}`}
                                >
                                  {c.correlation != null
                                    ? c.correlation.toFixed(3)
                                    : "—"}
                                </div>
                                <div className="text-[10px] text-slate-500">
                                  {corrLabel(c.correlation)}
                                </div>
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-400">
                                {c.r_squared != null
                                  ? c.r_squared.toFixed(3)
                                  : "—"}
                              </td>
                              <td className="py-2 pr-4 text-right">
                                <div className="text-slate-300">
                                  {c.beta != null ? c.beta.toFixed(3) : "—"}
                                </div>
                                <div className="text-[10px] text-slate-500">
                                  {betaLabel(c.beta)}
                                </div>
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-300 font-semibold">
                                {c.leverage_ratio != null
                                  ? `${c.leverage_ratio.toFixed(2)}×`
                                  : "—"}
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-400">
                                {c.stock_volatility_pct != null
                                  ? `${c.stock_volatility_pct.toFixed(2)}%`
                                  : "—"}
                              </td>
                              <td
                                className={`py-2 pr-4 text-right font-semibold ${pctColor(
                                  c.stock_pct_change,
                                )}`}
                              >
                                {fmtPct(c.stock_pct_change)}
                              </td>
                              <td className="py-2 text-right">
                                {c.significant ? (
                                  <span
                                    className="text-emerald-400"
                                    title={`t = ${c.t_stat}`}
                                  >
                                    ✓
                                  </span>
                                ) : (
                                  <span
                                    className="text-slate-600"
                                    title={`t = ${c.t_stat ?? "n/a"}`}
                                  >
                                    —
                                  </span>
                                )}
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-500 mt-3 leading-relaxed">
                  <strong className="text-slate-400">Correlation (r):</strong>{" "}
                  how closely the stock&apos;s daily returns track the
                  metal&apos;s (−1 to +1).{" "}
                  <strong className="text-slate-400">R²:</strong> share of stock
                  variance explained by the metal.{" "}
                  <strong className="text-slate-400">Beta:</strong> how much a
                  1% metal move historically moves the stock — &gt;1 means
                  amplified.{" "}
                  <strong className="text-slate-400">Leverage:</strong> stock
                  volatility ÷ metal volatility — the raw amplitude ratio.{" "}
                  <strong className="text-slate-400">Sig.:</strong> 95%
                  confidence the correlation is non-zero.
                </p>
              </div>

              {/* Heatmap */}
              {data.heatmap && data.heatmap.labels.length > 1 && (
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-4">
                    Pairwise Correlation Heatmap
                  </h2>
                  <Heatmap data={data.heatmap} />
                  <p className="text-xs text-slate-500 mt-3">
                    Each cell is the Pearson correlation of daily returns
                    between two assets. Green = positive, red = negative. The
                    final row/column is the metal itself.
                  </p>
                </div>
              )}
            </>
          )}

          {data && !data.message && data.companies.length === 0 && !loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              None of the selected companies have enough overlapping price
              history in this window. Try a longer window or different
              companies.
            </div>
          )}
        </div>
      </section>
    </>
  );
}
