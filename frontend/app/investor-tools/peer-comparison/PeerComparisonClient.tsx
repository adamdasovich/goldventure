"use client";

import { useState, useCallback } from "react";
import CompanyMultiPicker from "@/components/ui/CompanyMultiPicker";
import type { PickableCompany } from "@/components/ui/CompanyPicker";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";
import { useCompanyList } from "@/lib/useCompanyList";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface Peer {
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  stock_price: number | null;
  currency: string;
  market_cap_usd: number | null;
  total_gold_oz: number | null;
  total_silver_oz: number | null;
  avg_grade_gpt: number | null;
  total_tonnes: number | null;
  ev_per_oz: number | null;
  npv_usd_m: number | null;
  p_nav: number | null;
  irr_pct: number | null;
  aisc: number | null;
  total_financing_usd: number | null;
  project_count: number | null;
  flagship_stage: string | null;
}

interface PeerComparisonResponse {
  peers: Peer[];
  count: number;
  target_id: number;
}

type MetricKey = keyof Peer;

interface MetricRow {
  label: string;
  key: MetricKey;
  format: (v: unknown) => string;
  bestFn: "max" | "min" | "none";
}

const fmt = {
  usd: (v: unknown) =>
    v != null
      ? `$${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : "--",
  usdShort: (v: unknown) =>
    v != null
      ? `$${(Number(v) / 1e6).toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`
      : "--",
  usdM: (v: unknown) =>
    v != null
      ? `$${Number(v).toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`
      : "--",
  number: (v: unknown) =>
    v != null ? Number(v).toLocaleString("en-US") : "--",
  decimal: (v: unknown) =>
    v != null
      ? Number(v).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "--",
  pct: (v: unknown) => (v != null ? `${Number(v).toFixed(1)}%` : "--"),
  ratio: (v: unknown) => (v != null ? `${Number(v).toFixed(2)}x` : "--"),
  text: (v: unknown) => (v != null && v !== "" ? String(v) : "--"),
  int: (v: unknown) => (v != null ? String(Math.round(Number(v))) : "--"),
  grade: (v: unknown) => (v != null ? `${Number(v).toFixed(2)} g/t` : "--"),
};

const METRICS: MetricRow[] = [
  { label: "Stock Price", key: "stock_price", format: fmt.usd, bestFn: "max" },
  {
    label: "Market Cap",
    key: "market_cap_usd",
    format: fmt.usdShort,
    bestFn: "max",
  },
  {
    label: "Total Gold Oz",
    key: "total_gold_oz",
    format: fmt.number,
    bestFn: "max",
  },
  {
    label: "Avg Grade",
    key: "avg_grade_gpt",
    format: fmt.grade,
    bestFn: "max",
  },
  { label: "EV/oz", key: "ev_per_oz", format: fmt.usd, bestFn: "min" },
  { label: "NPV ($M)", key: "npv_usd_m", format: fmt.usdM, bestFn: "max" },
  { label: "P/NAV", key: "p_nav", format: fmt.ratio, bestFn: "min" },
  { label: "IRR%", key: "irr_pct", format: fmt.pct, bestFn: "max" },
  { label: "AISC", key: "aisc", format: fmt.usd, bestFn: "min" },
  {
    label: "Total Financing",
    key: "total_financing_usd",
    format: fmt.usdShort,
    bestFn: "max",
  },
  {
    label: "Project Count",
    key: "project_count",
    format: fmt.int,
    bestFn: "max",
  },
  {
    label: "Flagship Stage",
    key: "flagship_stage",
    format: fmt.text,
    bestFn: "none",
  },
];

function getBestIndex(
  peers: Peer[],
  key: MetricKey,
  bestFn: "max" | "min" | "none",
): number | null {
  if (bestFn === "none") return null;
  let bestIdx: number | null = null;
  let bestVal: number | null = null;
  for (let i = 0; i < peers.length; i++) {
    const raw = peers[i][key];
    if (raw == null) continue;
    const v = Number(raw);
    if (isNaN(v)) continue;
    if (bestVal === null || (bestFn === "max" ? v > bestVal : v < bestVal)) {
      bestVal = v;
      bestIdx = i;
    }
  }
  return bestIdx;
}

function SkeletonTable() {
  return (
    <div className="glass-card rounded-xl p-6 animate-pulse">
      <div className="h-6 w-48 bg-slate-700/50 rounded mb-6" />
      <div className="space-y-3">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-5 w-32 bg-slate-700/40 rounded" />
            <div className="h-5 flex-1 bg-slate-700/30 rounded" />
            <div className="h-5 flex-1 bg-slate-700/30 rounded" />
            <div className="h-5 flex-1 bg-slate-700/30 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PeerComparisonClient() {
  const [searchInput, setSearchInput] = useState("");
  const { companies, loading: companiesLoading } = useCompanyList();
  const [manualPeers, setManualPeers] = useState<PickableCompany[]>([]);
  const [data, setData] = useState<PeerComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = useCallback(
    async (params: Record<string, string>) => {
      setLoading(true);
      setError(null);
      setData(null);
      try {
        const result = await toolsAPI.peerComparison(params);
        setData(result as PeerComparisonResponse);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load peer comparison data.",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const handleCompare = () => {
    const trimmed = searchInput.trim();
    if (!trimmed) return;
    fetchComparison({ company_id: trimmed });
  };

  const handleManualCompare = () => {
    if (manualPeers.length === 0) return;
    fetchComparison({ company_ids: manualPeers.map((c) => c.id).join(",") });
  };

  const handleKeyDown = (e: React.KeyboardEvent, handler: () => void) => {
    if (e.key === "Enter") handler();
  };

  return (
    <>

      {/* Search Controls */}
      <section className="px-4 sm:px-6 lg:px-8 pb-6">
        <div className="max-w-5xl mx-auto space-y-4">
          {/* Primary: single company lookup */}
          <div className="glass-card rounded-xl p-5">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Search by Company Name or ID
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => handleKeyDown(e, handleCompare)}
                placeholder="e.g. Barrick Gold or 42"
                className="flex-1 bg-slate-800/60 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-gold-500/60 focus:ring-1 focus:ring-gold-500/30 transition-all"
              />
              <Button
                variant="primary"
                size="md"
                onClick={handleCompare}
                disabled={loading || !searchInput.trim()}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Loading
                  </span>
                ) : (
                  "Compare"
                )}
              </Button>
            </div>
          </div>

          {/* Secondary: manual multi-company */}
          <div className="glass-card rounded-xl p-5">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Build your own peer group
            </label>
            <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
              <div className="flex-1">
                <CompanyMultiPicker
                  companies={companies}
                  selected={manualPeers}
                  onChange={setManualPeers}
                  label=""
                  max={10}
                  disabled={companiesLoading}
                />
              </div>
              <Button
                variant="secondary"
                size="md"
                onClick={handleManualCompare}
                disabled={loading || manualPeers.length === 0}
              >
                Compare
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Error */}
      {error && (
        <section className="px-4 sm:px-6 lg:px-8 pb-6">
          <div className="max-w-5xl mx-auto">
            <div className="glass-card rounded-xl p-5 border-error/30">
              <p className="text-error text-sm">{error}</p>
            </div>
          </div>
        </section>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <section className="px-4 sm:px-6 lg:px-8 pb-8">
          <div className="max-w-5xl mx-auto">
            <SkeletonTable />
          </div>
        </section>
      )}

      {/* Results Table */}
      {data && !loading && (
        <section className="px-4 sm:px-6 lg:px-8 pb-12">
          <div className="max-w-[90rem] mx-auto">
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-lg font-semibold text-slate-200">
                Comparison Results
              </h2>
              <Badge variant="slate">{data.count} companies</Badge>
              <ExportButton
                className="ml-auto"
                filename="peer-comparison"
                rows={data.peers}
                columns={[
                  { label: "Company", value: (p) => p.company_name },
                  { label: "Ticker", value: (p) => p.ticker },
                  { label: "Exchange", value: (p) => p.exchange },
                  { label: "Price", value: (p) => p.stock_price },
                  { label: "Currency", value: (p) => p.currency },
                  { label: "Market cap USD", value: (p) => p.market_cap_usd },
                  { label: "Gold oz", value: (p) => p.total_gold_oz },
                  { label: "Silver oz", value: (p) => p.total_silver_oz },
                  { label: "Avg grade g/t", value: (p) => p.avg_grade_gpt },
                  { label: "Tonnes", value: (p) => p.total_tonnes },
                  { label: "EV/oz", value: (p) => p.ev_per_oz },
                  { label: "NPV USD M", value: (p) => p.npv_usd_m },
                  { label: "P/NAV", value: (p) => p.p_nav },
                  { label: "IRR %", value: (p) => p.irr_pct },
                  { label: "AISC", value: (p) => p.aisc },
                  {
                    label: "Financing USD",
                    value: (p) => p.total_financing_usd,
                  },
                  { label: "Projects", value: (p) => p.project_count },
                  { label: "Flagship stage", value: (p) => p.flagship_stage },
                ]}
              />
            </div>

            <div className="glass-card rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  {/* Column Headers: Company Names */}
                  <thead>
                    <tr className="border-b border-slate-700/50">
                      <th className="text-left px-4 py-3 text-slate-400 font-medium sticky left-0 bg-slate-900/90 backdrop-blur-sm z-10 min-w-[150px]">
                        Metric
                      </th>
                      {data.peers.map((peer) => {
                        const isTarget = peer.company_id === data.target_id;
                        return (
                          <th
                            key={peer.company_id}
                            className={`text-center px-4 py-3 min-w-[140px] ${
                              isTarget
                                ? "bg-gold-500/10 border-x border-gold-500/20"
                                : ""
                            }`}
                          >
                            <div className="flex flex-col items-center gap-1">
                              <span
                                className={`font-semibold ${
                                  isTarget ? "text-gold-400" : "text-slate-200"
                                }`}
                              >
                                {peer.company_name}
                              </span>
                              <span className="text-xs text-slate-500">
                                {peer.exchange}:{peer.ticker}
                              </span>
                              {isTarget && (
                                <Badge
                                  variant="gold"
                                  className="text-[9px] mt-0.5"
                                >
                                  Target
                                </Badge>
                              )}
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>

                  {/* Metric Rows */}
                  <tbody>
                    {METRICS.map((metric, rowIdx) => {
                      const bestIdx = getBestIndex(
                        data.peers,
                        metric.key,
                        metric.bestFn,
                      );
                      return (
                        <tr
                          key={metric.key}
                          className={`border-b border-slate-800/50 ${
                            rowIdx % 2 === 0 ? "bg-slate-800/10" : ""
                          } hover:bg-slate-800/30 transition-colors`}
                        >
                          <td className="px-4 py-3 text-slate-300 font-medium sticky left-0 bg-slate-900/90 backdrop-blur-sm z-10">
                            {metric.label}
                          </td>
                          {data.peers.map((peer, colIdx) => {
                            const isTarget = peer.company_id === data.target_id;
                            const isBest = bestIdx === colIdx;
                            const value = peer[metric.key];
                            return (
                              <td
                                key={peer.company_id}
                                className={`px-4 py-3 text-center font-mono text-sm ${
                                  isTarget
                                    ? "bg-gold-500/10 border-x border-gold-500/20"
                                    : ""
                                } ${
                                  isBest && value != null
                                    ? "text-emerald-400"
                                    : "text-slate-300"
                                }`}
                              >
                                <span
                                  className={
                                    isBest && value != null
                                      ? "bg-emerald-500/10 px-2 py-0.5 rounded"
                                      : ""
                                  }
                                >
                                  {metric.format(value)}
                                </span>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-6 mt-4 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-gold-500/20 border border-gold-500/30" />
                Target company
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-emerald-500/20 border border-emerald-500/30" />
                Best in class
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-500">--</span>
                Data unavailable
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Empty state */}
      {!data && !loading && !error && (
        <section className="px-4 sm:px-6 lg:px-8 pb-12">
          <div className="max-w-5xl mx-auto">
            <div className="glass-card rounded-xl p-12 text-center">
              <svg
                className="w-16 h-16 mx-auto text-slate-600 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <h3 className="text-lg font-medium text-slate-300 mb-2">
                Search for a company to get started
              </h3>
              <p className="text-sm text-slate-500 max-w-md mx-auto">
                Enter a company name or ID above and we will automatically find
                similar peers for a side-by-side comparison across key valuation
                metrics.
              </p>
            </div>
          </div>
        </section>
      )}
    </>
  );
}
