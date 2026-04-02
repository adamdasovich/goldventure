"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { toolsAPI } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";

interface GradeResult {
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  project_name: string;
  project_stage: string;
  country: string;
  commodity: string;
  grade: number;
  grade_unit: string;
  ounces: number;
  tonnes: number;
  gold_oz: number;
  silver_oz: number;
  npv_usd_m: number;
  irr_pct: number;
  aisc: number;
  stock_price: number;
  currency: string;
}

interface GradeRankerResponse {
  results: GradeResult[];
  count: number;
  commodities: string[];
  stages: string[];
}

const SORT_OPTIONS = [
  { value: "grade", label: "Grade (Highest)" },
  { value: "ounces", label: "Ounces (Largest)" },
  { value: "npv", label: "NPV (Highest)" },
  { value: "aisc", label: "AISC (Lowest)" },
];

const DEFAULT_COMMODITIES = [
  "Gold",
  "Silver",
  "Copper",
  "Lithium",
  "Uranium",
  "Nickel",
  "Zinc",
  "Cobalt",
  "Platinum",
  "Palladium",
];

function formatNumber(val: number | null | undefined, decimals = 2): string {
  if (val == null || isNaN(val)) return "--";
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
  return val.toFixed(decimals);
}

function formatCurrency(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "--";
  return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function gradeColorClass(grade: number, maxGrade: number): string {
  if (maxGrade === 0) return "text-slate-300";
  const ratio = grade / maxGrade;
  if (ratio >= 0.75) return "text-emerald-400 font-semibold";
  if (ratio >= 0.5) return "text-emerald-500/80";
  if (ratio >= 0.25) return "text-slate-300";
  return "text-slate-400";
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-700/50">
      {Array.from({ length: 9 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700/60 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  );
}

export default function GradeRankerPage() {
  const [data, setData] = useState<GradeRankerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [commodity, setCommodity] = useState("");
  const [sortBy, setSortBy] = useState("grade");
  const [stage, setStage] = useState("");
  const [minOunces, setMinOunces] = useState("");

  const [availableCommodities, setAvailableCommodities] =
    useState<string[]>(DEFAULT_COMMODITIES);
  const [availableStages, setAvailableStages] = useState<string[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (commodity) params.commodity = commodity;
      if (sortBy) params.sort = sortBy;
      if (stage) params.stage = stage;
      if (minOunces) params.min_ounces = minOunces;

      const res = await toolsAPI.gradeRanker(params);
      setData(res);
      if (res.commodities?.length) setAvailableCommodities(res.commodities);
      if (res.stages?.length) setAvailableStages(res.stages);
    } catch (err: any) {
      setError(err?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [commodity, sortBy, stage, minOunces]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const maxGrade = data?.results?.length
    ? Math.max(...data.results.map((r) => r.grade ?? 0))
    : 0;

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
      <section className="py-10 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto">
          <Link
            href="/investor-tools"
            className="inline-flex items-center text-sm text-slate-400 hover:text-gold-400 transition-colors mb-4"
          >
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Investor Tools
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gold-500/15 border border-gold-500/30">
              <svg
                className="w-5 h-5 text-gold-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
                />
              </svg>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold">
              Resource Grade Ranker
            </h1>
          </div>
          <p className="text-slate-400 max-w-2xl">
            Rank companies by resource grade, size, NPV, and cost metrics. Find
            the highest-grade deposits across all commodities.
          </p>
        </div>
      </section>

      {/* Filters */}
      <section className="px-4 sm:px-6 lg:px-8 pb-4">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
              {/* Commodity */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Commodity
                </label>
                <select
                  value={commodity}
                  onChange={(e) => setCommodity(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500 transition-colors"
                >
                  <option value="">All Commodities</option>
                  {availableCommodities.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sort By */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500 transition-colors"
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Stage */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Stage
                </label>
                <select
                  value={stage}
                  onChange={(e) => setStage(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500 transition-colors"
                >
                  <option value="">All Stages</option>
                  {availableStages.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Ounces */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Min Ounces
                </label>
                <input
                  type="number"
                  value={minOunces}
                  onChange={(e) => setMinOunces(e.target.value)}
                  placeholder="e.g. 100000"
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-gold-500 transition-colors"
                />
              </div>

              {/* Apply */}
              <div>
                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  onClick={fetchData}
                >
                  Apply Filters
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto">
          {/* Count */}
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-slate-400">
              {loading
                ? "Loading results..."
                : data
                  ? `${data.count} project${data.count !== 1 ? "s" : ""} found`
                  : ""}
            </p>
            {commodity && <Badge variant="gold">{commodity}</Badge>}
          </div>

          {/* Error */}
          {error && (
            <div className="glass-card rounded-xl p-6 text-center">
              <p className="text-red-400 mb-3">{error}</p>
              <Button variant="secondary" size="sm" onClick={fetchData}>
                Retry
              </Button>
            </div>
          )}

          {/* Table */}
          {!error && (
            <div className="glass-card rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Rank
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Company
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Project
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Stage
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Grade
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Ounces
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        NPV ($M)
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        AISC ($/oz)
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Stock Price
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading &&
                      Array.from({ length: 10 }).map((_, i) => (
                        <SkeletonRow key={i} />
                      ))}

                    {!loading &&
                      data?.results?.map((row, idx) => (
                        <tr
                          key={`${row.company_id}-${row.project_name}-${idx}`}
                          className="border-b border-slate-700/50 hover:bg-slate-800/40 transition-colors"
                        >
                          {/* Rank */}
                          <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                            {idx + 1}
                          </td>

                          {/* Company */}
                          <td className="px-4 py-3">
                            <Link
                              href={`/companies/${row.company_id}`}
                              className="text-gold-400 hover:text-gold-300 font-medium transition-colors"
                            >
                              {row.company_name}
                            </Link>
                            <div className="text-xs text-slate-500 mt-0.5">
                              {row.exchange}:{row.ticker}
                            </div>
                          </td>

                          {/* Project */}
                          <td className="px-4 py-3">
                            <span className="text-slate-200">
                              {row.project_name || "--"}
                            </span>
                            {row.country && (
                              <div className="text-xs text-slate-500 mt-0.5">
                                {row.country}
                              </div>
                            )}
                          </td>

                          {/* Stage */}
                          <td className="px-4 py-3">
                            <Badge
                              variant={
                                row.project_stage
                                  ?.toLowerCase()
                                  .includes("produc")
                                  ? "success"
                                  : row.project_stage
                                        ?.toLowerCase()
                                        .includes("feasib")
                                    ? "info"
                                    : "slate"
                              }
                            >
                              {row.project_stage || "--"}
                            </Badge>
                          </td>

                          {/* Grade */}
                          <td
                            className={`px-4 py-3 text-right font-mono ${gradeColorClass(row.grade ?? 0, maxGrade)}`}
                          >
                            {row.grade != null ? row.grade.toFixed(2) : "--"}
                            {row.grade_unit && (
                              <span className="text-xs text-slate-500 ml-1">
                                {row.grade_unit}
                              </span>
                            )}
                          </td>

                          {/* Ounces */}
                          <td className="px-4 py-3 text-right text-slate-300 font-mono">
                            {formatNumber(row.ounces, 0)}
                          </td>

                          {/* NPV */}
                          <td className="px-4 py-3 text-right text-slate-300 font-mono">
                            {row.npv_usd_m != null
                              ? `$${formatNumber(row.npv_usd_m, 1)}`
                              : "--"}
                          </td>

                          {/* AISC */}
                          <td className="px-4 py-3 text-right text-slate-300 font-mono">
                            {row.aisc != null ? formatCurrency(row.aisc) : "--"}
                          </td>

                          {/* Stock Price */}
                          <td className="px-4 py-3 text-right text-slate-200 font-mono">
                            {row.stock_price != null
                              ? `${formatCurrency(row.stock_price)} ${row.currency || ""}`
                              : "--"}
                          </td>
                        </tr>
                      ))}

                    {!loading && data?.results?.length === 0 && (
                      <tr>
                        <td
                          colSpan={9}
                          className="px-4 py-12 text-center text-slate-500"
                        >
                          No results found. Try adjusting your filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
