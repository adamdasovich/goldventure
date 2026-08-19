"use client";

import { useState, useEffect, useCallback } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";
import Link from "next/link";

/* ---------- types ---------- */

interface DrillResult {
  id: number;
  company_id: number;
  company_name: string;
  ticker: string;
  title: string;
  published_date: string;
  url: string;
}

interface ActiveDriller {
  company_name: string;
  ticker: string;
  count: number;
}

interface DrillData {
  results: DrillResult[];
  count: number;
  most_active_drillers: ActiveDriller[];
  period_days: number;
}

/* ---------- constants ---------- */

const DAY_OPTIONS = [14, 30, 60, 90] as const;

const COMMODITIES = [
  { value: "", label: "All Commodities" },
  { value: "gold", label: "Gold" },
  { value: "silver", label: "Silver" },
  { value: "copper", label: "Copper" },
  { value: "lithium", label: "Lithium" },
  { value: "uranium", label: "Uranium" },
];

/* ---------- skeleton ---------- */

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-slate-700/50 ${className}`} />
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
        {/* main list skeleton */}
        <div className="space-y-4">
          <Skeleton className="h-6 w-48 mb-2" />
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass-card rounded-xl p-4">
              <Skeleton className="h-5 w-3/4 mb-3" />
              <div className="flex items-center gap-3">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-4 w-24 ml-auto" />
              </div>
            </div>
          ))}
        </div>
        {/* sidebar skeleton */}
        <div className="glass-card rounded-xl p-5 h-fit">
          <Skeleton className="h-5 w-40 mb-4" />
          <div className="space-y-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-5 w-8" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- page ---------- */

export default function DrillScannerClient() {
  const [days, setDays] = useState<number>(30);
  const [commodity, setCommodity] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [data, setData] = useState<DrillData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* debounce company search */
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { days: String(days) };
      if (commodity) params.commodity = commodity;
      if (debouncedSearch) params.company = debouncedSearch;
      const res = await toolsAPI.drillScanner(params);
      setData(res as DrillData);
    } catch (e: any) {
      setError(e?.message || "Failed to load drill results.");
    } finally {
      setLoading(false);
    }
  }, [days, commodity, debouncedSearch]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <>
      {/* Filters */}
      <section className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-3">
          {/* Day selector */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-slate-400 mr-1">Period:</span>
            {DAY_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  days === d
                    ? "bg-gold-500/20 text-gold-400 border border-gold-500/40"
                    : "bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:text-slate-200"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>

          {/* Commodity filter */}
          <select
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            className="bg-slate-800/60 border border-slate-700/50 text-slate-300 text-sm rounded-md px-3 py-1.5 focus:border-gold-500/50 focus:outline-none"
          >
            {COMMODITIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>

          {/* Company search */}
          <div className="relative">
            <svg
              className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search company..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-800/60 border border-slate-700/50 text-slate-300 text-sm rounded-md pl-8 pr-3 py-1.5 w-48 focus:border-gold-500/50 focus:outline-none placeholder:text-slate-500"
            />
          </div>
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
        ) : data && data.results.length > 0 ? (
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
              {/* Main results list */}
              <div>
                <div className="flex items-center justify-between gap-3 mb-4">
                  <p className="text-sm text-slate-400">
                    <span className="text-gold-400 font-semibold">
                      {data.count.toLocaleString()}
                    </span>{" "}
                    drill result{data.count !== 1 ? "s" : ""} in the last{" "}
                    {data.period_days} days
                  </p>
                  <ExportButton
                    filename="drill-results"
                    rows={data.results}
                    columns={[
                      { label: "Date", value: (r) => r.published_date },
                      { label: "Company", value: (r) => r.company_name },
                      { label: "Ticker", value: (r) => r.ticker },
                      { label: "Headline", value: (r) => r.title },
                      { label: "URL", value: (r) => r.url },
                    ]}
                  />
                </div>

                <div className="space-y-3">
                  {data.results.map((r) => (
                    <div
                      key={r.id}
                      className="glass-card rounded-xl px-5 py-4 border border-slate-700/30 hover:border-gold-500/20 transition-colors"
                    >
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-slate-100 hover:text-gold-400 transition-colors leading-snug line-clamp-2"
                      >
                        {r.title}
                        <svg
                          className="inline-block ml-1.5 w-3.5 h-3.5 text-slate-500 -mt-0.5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                          />
                        </svg>
                      </a>
                      <div className="flex items-center gap-3 mt-2.5">
                        <Link
                          href={`/companies/${r.company_id}`}
                          className="text-xs text-slate-300 hover:text-gold-400 transition-colors"
                        >
                          {r.company_name}
                        </Link>
                        <Badge variant="slate">{r.ticker}</Badge>
                        <span className="text-xs text-slate-500 ml-auto">
                          {new Date(r.published_date).toLocaleDateString(
                            "en-US",
                            {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            },
                          )}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sidebar: Most Active Drillers */}
              <div className="glass-card rounded-xl p-5 h-fit lg:sticky lg:top-24">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  Most Active Drillers
                </h2>
                {data.most_active_drillers.length > 0 ? (
                  <div className="space-y-2.5">
                    {data.most_active_drillers.slice(0, 10).map((d, i) => (
                      <div
                        key={`${d.ticker}-${i}`}
                        className="flex items-center justify-between gap-2"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="text-xs text-slate-500 w-4 text-right shrink-0">
                            {i + 1}
                          </span>
                          <span className="text-sm text-slate-200 truncate">
                            {d.company_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant="slate">{d.ticker}</Badge>
                          <span className="text-xs font-medium text-gold-400 w-6 text-right">
                            {d.count}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No data available.</p>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Empty state */
          <div className="max-w-7xl mx-auto">
            <div className="glass-card rounded-xl p-12 text-center">
              <svg
                className="mx-auto w-12 h-12 text-slate-600 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                />
              </svg>
              <p className="text-slate-400 mb-1">
                No drill results found for the selected filters.
              </p>
              <p className="text-xs text-slate-500">
                Try adjusting the time period, commodity, or search term.
              </p>
            </div>
          </div>
        )}
      </section>
    </>
  );
}
