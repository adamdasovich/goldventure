"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface MonthlyTrend {
  month: string;
  count: number;
  total_usd: number;
}

interface ByType {
  type: string;
  count: number;
  total_usd: number;
  avg_usd: number;
}

interface ByCommodity {
  commodity: string;
  count: number;
  total_usd: number;
}

interface TopCompany {
  company_id: number;
  company_name: string;
  ticker: string;
  count: number;
  total_usd: number;
}

interface RecentDeal {
  id: number;
  company_id: number;
  company_name: string;
  ticker: string;
  type: string;
  amount_usd: number;
  price_per_share: number | null;
  announced_date: string;
  status: string;
  has_warrants: boolean;
}

interface FlowData {
  monthly_trend: MonthlyTrend[];
  by_type: ByType[];
  by_commodity: ByCommodity[];
  top_companies: TopCompany[];
  recent: RecentDeal[];
  summary: { total_count: number; total_usd: number; period_months: number };
  financing_types: string[];
}

/* ---------- helpers ---------- */

function formatUSD(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

function formatType(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function monthLabel(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

/* ---------- skeleton ---------- */

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-slate-700/50 ${className}`} />
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-5">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-8 w-32" />
          </div>
        ))}
      </div>
      {/* charts */}
      <div className="glass-card rounded-xl p-6">
        <Skeleton className="h-5 w-40 mb-4" />
        <div className="flex items-end gap-2 h-40">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="flex-1 animate-pulse rounded bg-slate-700/50"
              style={{ height: `${30 + Math.random() * 70}%` }}
            />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-6">
            <Skeleton className="h-5 w-32 mb-4" />
            <div className="space-y-3">
              {[...Array(4)].map((_, j) => (
                <Skeleton key={j} className="h-6 w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- page ---------- */

const MONTH_OPTIONS = [3, 6, 12] as const;

export default function FinancingFlowClient() {
  const [months, setMonths] = useState<number>(6);
  const [commodityFilter, setCommodityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [data, setData] = useState<FlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { months: String(months) };
      if (commodityFilter) params.commodity = commodityFilter;
      if (typeFilter) params.type = typeFilter;
      const res = await toolsAPI.financingFlow(params);
      setData(res as FlowData);
    } catch (e: any) {
      setError(e?.message || "Failed to load financing data.");
    } finally {
      setLoading(false);
    }
  }, [months, commodityFilter, typeFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  /* derived values for chart scaling */
  const maxMonthly = data
    ? Math.max(...data.monthly_trend.map((m) => m.total_usd), 1)
    : 1;
  const maxByType = data
    ? Math.max(...data.by_type.map((t) => t.total_usd), 1)
    : 1;
  const maxByCommodity = data
    ? Math.max(...data.by_commodity.map((c) => c.total_usd), 1)
    : 1;

  /* unique commodities for filter dropdown (derived from by_commodity) */
  const commodities = data ? data.by_commodity.map((c) => c.commodity) : [];
  const types = data ? data.financing_types : [];

  return (
    <>
      {/* Filters */}
      <section className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-3">
          {/* Month selector */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-slate-400 mr-1">Period:</span>
            {MONTH_OPTIONS.map((m) => (
              <button
                key={m}
                onClick={() => setMonths(m)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  months === m
                    ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                    : "bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:text-slate-200"
                }`}
              >
                {m}mo
              </button>
            ))}
          </div>

          {/* Commodity filter */}
          <select
            value={commodityFilter}
            onChange={(e) => setCommodityFilter(e.target.value)}
            className="bg-slate-800/60 border border-slate-700/50 text-slate-300 text-sm rounded-md px-3 py-1.5 focus:border-gold-500/50 focus:outline-none"
          >
            <option value="">All Commodities</option>
            {commodities.map((c) => (
              <option key={c} value={c}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>

          {/* Type filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-800/60 border border-slate-700/50 text-slate-300 text-sm rounded-md px-3 py-1.5 focus:border-gold-500/50 focus:outline-none"
          >
            <option value="">All Types</option>
            {types.map((t) => (
              <option key={t} value={t}>
                {formatType(t)}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Content */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <div className="max-w-7xl mx-auto">
            <div className="glass-card rounded-xl p-8 text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <Button variant="secondary" size="sm" onClick={fetchData}>
                Retry
              </Button>
            </div>
          </div>
        ) : data ? (
          <div className="max-w-7xl mx-auto space-y-8">
            {/* ---- Summary Stats ---- */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="glass-card rounded-xl p-5">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  Total Financings
                </p>
                <p className="text-2xl font-bold text-white">
                  {data.summary.total_count.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  last {data.summary.period_months} months
                </p>
              </div>
              <div className="glass-card rounded-xl p-5">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  Total Raised
                </p>
                <p className="text-2xl font-bold text-gold-400">
                  {formatUSD(data.summary.total_usd)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  last {data.summary.period_months} months
                </p>
              </div>
              <div className="glass-card rounded-xl p-5">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  Avg Deal Size
                </p>
                <p className="text-2xl font-bold text-white">
                  {data.summary.total_count > 0
                    ? formatUSD(
                        data.summary.total_usd / data.summary.total_count,
                      )
                    : "$0"}
                </p>
                <p className="text-xs text-slate-500 mt-1">per financing</p>
              </div>
            </div>

            {/* ---- Monthly Trend ---- */}
            {data.monthly_trend.length > 0 && (
              <div className="glass-card rounded-xl p-6">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  Monthly Trend
                </h2>
                <div className="flex items-end gap-2 h-48">
                  {data.monthly_trend.map((m) => {
                    const pct = (m.total_usd / maxMonthly) * 100;
                    return (
                      <div
                        key={m.month}
                        className="flex-1 flex flex-col items-center gap-1 min-w-0"
                      >
                        <span className="text-[10px] text-slate-400 truncate">
                          {formatUSD(m.total_usd)}
                        </span>
                        <div
                          className="w-full flex justify-center"
                          style={{ height: "160px" }}
                        >
                          <div
                            className="w-full max-w-[48px] rounded-t bg-gradient-to-t from-gold-600 to-gold-400 transition-all duration-500 self-end"
                            style={{ height: `${Math.max(pct, 2)}%` }}
                            title={`${m.count} deals - ${formatUSD(m.total_usd)}`}
                          />
                        </div>
                        <span className="text-[10px] text-slate-500">
                          {monthLabel(m.month)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ---- By Type & By Commodity side by side ---- */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* By Type */}
              {data.by_type.length > 0 && (
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-4">
                    By Financing Type
                  </h2>
                  <div className="space-y-3">
                    {data.by_type.map((t) => {
                      const pct = (t.total_usd / maxByType) * 100;
                      return (
                        <div key={t.type}>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-slate-200 truncate mr-2">
                              {formatType(t.type)}
                            </span>
                            <span className="text-slate-400 whitespace-nowrap">
                              {t.count} deals &middot; {formatUSD(t.total_usd)}
                            </span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-slate-800/80">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-gold-600 to-gold-400 transition-all duration-500"
                              style={{ width: `${Math.max(pct, 1)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* By Commodity */}
              {data.by_commodity.length > 0 && (
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-4">
                    By Commodity
                  </h2>
                  <div className="space-y-3">
                    {data.by_commodity.map((c) => {
                      const pct = (c.total_usd / maxByCommodity) * 100;
                      return (
                        <div key={c.commodity}>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-slate-200 truncate mr-2 capitalize">
                              {c.commodity}
                            </span>
                            <span className="text-slate-400 whitespace-nowrap">
                              {c.count} deals &middot; {formatUSD(c.total_usd)}
                            </span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-slate-800/80">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-gold-600 to-gold-400 transition-all duration-500"
                              style={{ width: `${Math.max(pct, 1)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* ---- Top 10 Companies ---- */}
            {data.top_companies.length > 0 && (
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-sm font-semibold text-gold-400">
                    Top 10 Companies by Capital Raised
                  </h2>
                  <ExportButton
                    filename="financing-flow-top-companies"
                    rows={data.top_companies}
                    columns={[
                      { label: "Company", value: (c) => c.company_name },
                      { label: "Ticker", value: (c) => c.ticker },
                      { label: "Financings", value: (c) => c.count },
                      { label: "Total raised", value: (c) => c.total_usd },
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
                        <th className="text-right pb-2 pr-4">Deals</th>
                        <th className="text-right pb-2">Total Raised</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_companies.map((c, i) => (
                        <tr
                          key={c.company_id}
                          className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="py-2 pr-4 text-slate-500">{i + 1}</td>
                          <td className="py-2 pr-4">
                            <Link
                              href={`/companies/${c.company_id}`}
                              className="text-slate-200 hover:text-gold-400 transition-colors"
                            >
                              {c.company_name}
                            </Link>
                          </td>
                          <td className="py-2 pr-4">
                            <Badge variant="slate">{c.ticker}</Badge>
                          </td>
                          <td className="py-2 pr-4 text-right text-slate-300">
                            {c.count}
                          </td>
                          <td className="py-2 text-right font-medium text-gold-400">
                            {formatUSD(c.total_usd)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ---- Recent Notable Deals ---- */}
            {data.recent.length > 0 && (
              <div className="glass-card rounded-xl p-6">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  Recent Notable Deals
                </h2>
                <div className="space-y-3">
                  {data.recent.map((d) => (
                    <div
                      key={d.id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3 rounded-lg bg-slate-800/30 border border-slate-700/30"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="min-w-0">
                          <Link
                            href={`/companies/${d.company_id}`}
                            className="text-sm font-medium text-slate-200 hover:text-gold-400 transition-colors truncate block"
                          >
                            {d.company_name}
                          </Link>
                          <div className="flex items-center gap-2 mt-0.5">
                            <Badge variant="slate">{d.ticker}</Badge>
                            <Badge variant="gold">{formatType(d.type)}</Badge>
                            {d.has_warrants && (
                              <Badge variant="warning">Warrants</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 sm:text-right shrink-0">
                        <div>
                          <p className="text-sm font-semibold text-gold-400">
                            {formatUSD(d.amount_usd)}
                          </p>
                          {d.price_per_share != null && (
                            <p className="text-[11px] text-slate-500">
                              @ ${d.price_per_share.toFixed(3)}/sh
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-400">
                            {new Date(d.announced_date).toLocaleDateString(
                              "en-US",
                              {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                              },
                            )}
                          </p>
                          <p className="text-[11px] text-slate-500 capitalize">
                            {d.status}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </section>
    </>
  );
}
