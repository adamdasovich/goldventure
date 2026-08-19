"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import CompanyMultiPicker from "@/components/ui/CompanyMultiPicker";
import type { PickableCompany } from "@/components/ui/CompanyPicker";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";
import { useCompanyList } from "@/lib/useCompanyList";

/* ---------- types ---------- */

interface Holding {
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  stock_price: number | null;
  change_pct: number | null;
  market_cap_usd: number | null;
  gold_oz: number | null;
  silver_oz: number | null;
  project_count: number;
  commodity: string;
  country: string;
  stage: string;
  open_financings: number;
}

interface ExposureItem {
  name: string;
  count: number;
  pct: number;
}

interface XrayData {
  holdings: Holding[];
  count: number;
  total_market_cap_usd: number;
  commodity_exposure: ExposureItem[];
  country_exposure: ExposureItem[];
  stage_exposure: ExposureItem[];
  dilution_risks: Holding[];
}

/* ---------- helpers ---------- */

function formatUSD(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toLocaleString();
}

function formatPct(value: number | null): string {
  if (value == null) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-5">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-8 w-32" />
          </div>
        ))}
      </div>
      <div className="glass-card rounded-xl p-6">
        <Skeleton className="h-5 w-40 mb-4" />
        <div className="space-y-3">
          {[...Array(5)].map((_, j) => (
            <Skeleton key={j} className="h-10 w-full" />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
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

/* ---------- exposure bar chart ---------- */

function ExposureChart({
  title,
  items,
}: {
  title: string;
  items: ExposureItem[];
}) {
  if (!items.length) return null;
  const maxPct = Math.max(...items.map((i) => i.pct), 1);

  return (
    <div className="glass-card rounded-xl p-6">
      <h2 className="text-sm font-semibold text-gold-400 mb-4">{title}</h2>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-slate-200 truncate mr-2 capitalize">
                {item.name || "Unknown"}
              </span>
              <span className="text-slate-400 whitespace-nowrap">
                {item.count} {item.count === 1 ? "company" : "companies"}{" "}
                &middot; {item.pct.toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800/80">
              <div
                className="h-full rounded-full bg-gradient-to-r from-gold-600 to-gold-400 transition-all duration-500"
                style={{
                  width: `${Math.max((item.pct / maxPct) * 100, 2)}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- page ---------- */

export default function PortfolioXrayClient() {
  const { companies, loading: companiesLoading } = useCompanyList();
  const [selected, setSelected] = useState<PickableCompany[]>([]);
  const [data, setData] = useState<XrayData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (selected.length === 0) {
      setError("Add at least one company to analyze.");
      return;
    }
    const cleaned = selected.map((c) => c.id).join(",");

    setLoading(true);
    setError(null);
    try {
      const res = await toolsAPI.portfolioXray({ company_ids: cleaned });
      setData(res as XrayData);
    } catch (e: any) {
      setError(e?.message || "Failed to analyze portfolio.");
    } finally {
      setLoading(false);
    }
  }

  const dilutionCount = data?.dilution_risks?.length ?? 0;

  return (
    <>

      {/* Input */}
      <section className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-6">
            <p className="text-xs text-slate-500 mb-3">
              Add the companies you hold, then analyze the set for commodity,
              geographic and stage concentration.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
              <div className="flex-1">
                <CompanyMultiPicker
                  companies={companies}
                  selected={selected}
                  onChange={setSelected}
                  label="Portfolio"
                  max={25}
                  disabled={companiesLoading}
                />
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={handleAnalyze}
                disabled={loading || selected.length === 0}
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
                    Analyzing...
                  </span>
                ) : (
                  "Analyze Portfolio"
                )}
              </Button>
            </div>
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
              <Button variant="secondary" size="sm" onClick={handleAnalyze}>
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
                  Total Companies
                </p>
                <p className="text-2xl font-bold text-white">{data.count}</p>
              </div>
              <div className="glass-card rounded-xl p-5">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  Total Market Cap
                </p>
                <p className="text-2xl font-bold text-gold-400">
                  {data.total_market_cap_usd
                    ? formatUSD(data.total_market_cap_usd)
                    : "—"}
                </p>
              </div>
              <div className="glass-card rounded-xl p-5">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  Dilution Risk
                </p>
                <p
                  className={`text-2xl font-bold ${dilutionCount > 0 ? "text-red-400" : "text-green-400"}`}
                >
                  {dilutionCount}{" "}
                  <span className="text-sm font-normal text-slate-400">
                    {dilutionCount === 1 ? "company" : "companies"}
                  </span>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  with open financings
                </p>
              </div>
            </div>

            {/* ---- Holdings Table ---- */}
            {data.holdings.length > 0 && (
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between mb-4 gap-3">
                  <h2 className="text-sm font-semibold text-gold-400">
                    Holdings
                  </h2>
                  <ExportButton
                    filename="portfolio-xray"
                    rows={data.holdings}
                    columns={[
                      { label: "Company", value: (h) => h.company_name },
                      { label: "Ticker", value: (h) => h.ticker },
                      { label: "Exchange", value: (h) => h.exchange },
                      { label: "Price", value: (h) => h.stock_price },
                      { label: "Change %", value: (h) => h.change_pct },
                      {
                        label: "Market cap USD",
                        value: (h) => h.market_cap_usd,
                      },
                      { label: "Commodity", value: (h) => h.commodity },
                      { label: "Country", value: (h) => h.country },
                      { label: "Stage", value: (h) => h.stage },
                      { label: "Projects", value: (h) => h.project_count },
                      { label: "Gold oz", value: (h) => h.gold_oz },
                      { label: "Silver oz", value: (h) => h.silver_oz },
                      {
                        label: "Open financings",
                        value: (h) => h.open_financings,
                      },
                    ]}
                  />
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                        <th className="text-left pb-2 pr-3">Company</th>
                        <th className="text-left pb-2 pr-3">Ticker</th>
                        <th className="text-right pb-2 pr-3">Price</th>
                        <th className="text-right pb-2 pr-3">Change</th>
                        <th className="text-right pb-2 pr-3">Mkt Cap</th>
                        <th className="text-right pb-2 pr-3">Gold Oz</th>
                        <th className="text-left pb-2 pr-3">Commodity</th>
                        <th className="text-left pb-2 pr-3">Stage</th>
                        <th className="text-right pb-2">Financings</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.holdings.map((h) => (
                        <tr
                          key={h.company_id}
                          className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="py-2.5 pr-3">
                            <Link
                              href={`/companies/${h.company_id}`}
                              className="text-slate-200 hover:text-gold-400 transition-colors font-medium"
                            >
                              {h.company_name}
                            </Link>
                          </td>
                          <td className="py-2.5 pr-3">
                            <Badge variant="slate">
                              {h.ticker}
                              {h.exchange ? `:${h.exchange}` : ""}
                            </Badge>
                          </td>
                          <td className="py-2.5 pr-3 text-right text-slate-300 tabular-nums">
                            {h.stock_price != null
                              ? `$${h.stock_price.toFixed(2)}`
                              : "—"}
                          </td>
                          <td
                            className={`py-2.5 pr-3 text-right tabular-nums ${
                              h.change_pct != null && h.change_pct > 0
                                ? "text-green-400"
                                : h.change_pct != null && h.change_pct < 0
                                  ? "text-red-400"
                                  : "text-slate-400"
                            }`}
                          >
                            {formatPct(h.change_pct)}
                          </td>
                          <td className="py-2.5 pr-3 text-right text-slate-300 tabular-nums">
                            {h.market_cap_usd
                              ? formatUSD(h.market_cap_usd)
                              : "—"}
                          </td>
                          <td className="py-2.5 pr-3 text-right text-slate-300 tabular-nums">
                            {h.gold_oz ? formatNumber(h.gold_oz) : "—"}
                          </td>
                          <td className="py-2.5 pr-3 text-slate-300 capitalize">
                            {h.commodity || "—"}
                          </td>
                          <td className="py-2.5 pr-3 text-slate-300 capitalize">
                            {h.stage || "—"}
                          </td>
                          <td className="py-2.5 text-right">
                            {h.open_financings > 0 ? (
                              <Badge variant="error">{h.open_financings}</Badge>
                            ) : (
                              <span className="text-slate-500">0</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ---- Exposure Charts ---- */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ExposureChart
                title="Commodity Exposure"
                items={data.commodity_exposure}
              />
              <ExposureChart
                title="Country Exposure"
                items={data.country_exposure}
              />
              <ExposureChart
                title="Stage Exposure"
                items={data.stage_exposure}
              />
            </div>

            {/* ---- Dilution Risk Alert ---- */}
            {data.dilution_risks.length > 0 && (
              <div className="glass-card rounded-xl p-6 border border-red-500/30 bg-red-950/10">
                <div className="flex items-center gap-2 mb-4">
                  <svg
                    className="h-5 w-5 text-red-400 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                    />
                  </svg>
                  <h2 className="text-sm font-semibold text-red-400">
                    Dilution Risk Alert
                  </h2>
                </div>
                <p className="text-xs text-slate-400 mb-4">
                  These companies have open financings that may dilute existing
                  shareholders.
                </p>
                <div className="space-y-2">
                  {data.dilution_risks.map((h) => (
                    <div
                      key={h.company_id}
                      className="flex items-center justify-between px-4 py-2.5 rounded-lg bg-red-950/20 border border-red-500/20"
                    >
                      <div className="flex items-center gap-3">
                        <Link
                          href={`/companies/${h.company_id}`}
                          className="text-sm font-medium text-slate-200 hover:text-gold-400 transition-colors"
                        >
                          {h.company_name}
                        </Link>
                        <Badge variant="slate">{h.ticker}</Badge>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="error">
                          {h.open_financings} open{" "}
                          {h.open_financings === 1 ? "financing" : "financings"}
                        </Badge>
                        {h.market_cap_usd && (
                          <span className="text-xs text-slate-500">
                            Mkt Cap: {formatUSD(h.market_cap_usd)}
                          </span>
                        )}
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
