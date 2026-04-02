"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { toolsAPI } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";

interface Listing {
  id: number;
  slug: string;
  title: string;
  location: string;
  country: string;
  primary_mineral: string;
  exploration_stage: string;
  total_hectares: number;
  asking_price: number;
  price_currency: string;
  price_per_hectare: number;
  listing_type: string;
}

interface Benchmarks {
  avg_price_per_ha: number;
  min_price_per_ha: number;
  max_price_per_ha: number;
  median_price_per_ha: number;
  sample_size: number;
}

interface ValuationResponse {
  listings: Listing[];
  count: number;
  benchmarks: Benchmarks;
  filters: {
    minerals: string[];
    countries: string[];
  };
}

function formatPrice(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "--";
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
  return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function formatPricePerHa(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "--";
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
  return `$${val.toFixed(0)}`;
}

function formatHectares(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "--";
  return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function priceColorClass(pricePerHa: number, median: number): string {
  if (median <= 0) return "text-slate-300";
  if (pricePerHa <= median) return "text-emerald-400 font-semibold";
  return "text-amber-400 font-semibold";
}

function SkeletonCard() {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="h-3 w-20 bg-slate-700/60 rounded animate-pulse mb-3" />
      <div className="h-7 w-28 bg-slate-700/60 rounded animate-pulse" />
    </div>
  );
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

export default function PropertyValuationPage() {
  const [data, setData] = useState<ValuationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [mineral, setMineral] = useState("");
  const [country, setCountry] = useState("");

  const [availableMinerals, setAvailableMinerals] = useState<string[]>([]);
  const [availableCountries, setAvailableCountries] = useState<string[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (mineral) params.mineral = mineral;
      if (country) params.country = country;

      const res = await toolsAPI.propertyValuation(params);
      setData(res);
      if (res.filters?.minerals?.length)
        setAvailableMinerals(res.filters.minerals);
      if (res.filters?.countries?.length)
        setAvailableCountries(res.filters.countries);
    } catch (err: any) {
      setError(err?.message || "Failed to load valuation data");
    } finally {
      setLoading(false);
    }
  }, [mineral, country]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const median = data?.benchmarks?.median_price_per_ha ?? 0;

  const benchmarkCards = data?.benchmarks
    ? [
        {
          label: "Avg $/Hectare",
          value: formatPricePerHa(data.benchmarks.avg_price_per_ha),
        },
        {
          label: "Min $/Hectare",
          value: formatPricePerHa(data.benchmarks.min_price_per_ha),
        },
        {
          label: "Max $/Hectare",
          value: formatPricePerHa(data.benchmarks.max_price_per_ha),
        },
        {
          label: "Median $/Hectare",
          value: formatPricePerHa(data.benchmarks.median_price_per_ha),
        },
        {
          label: "Sample Size",
          value: data.benchmarks.sample_size.toLocaleString(),
        },
      ]
    : [];

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
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                />
              </svg>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold">
              Property Valuation
            </h1>
          </div>
          <p className="text-slate-400 max-w-2xl">
            Compare mining property valuations with price-per-hectare benchmarks
            across minerals and countries. Identify undervalued opportunities.
          </p>
        </div>
      </section>

      {/* Filters */}
      <section className="px-4 sm:px-6 lg:px-8 pb-4">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-end">
              {/* Mineral */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Mineral
                </label>
                <select
                  value={mineral}
                  onChange={(e) => setMineral(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500 transition-colors"
                >
                  <option value="">All Minerals</option>
                  {availableMinerals.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              {/* Country */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Country
                </label>
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500 transition-colors"
                >
                  <option value="">All Countries</option>
                  {availableCountries.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
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

      {/* Benchmarks */}
      <section className="px-4 sm:px-6 lg:px-8 pb-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">
            Valuation Benchmarks
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {loading &&
              Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)}
            {!loading &&
              benchmarkCards.map((card) => (
                <div key={card.label} className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 mb-1">{card.label}</p>
                  <p className="text-xl font-bold text-gold-400">
                    {card.value}
                  </p>
                </div>
              ))}
            {!loading && !data?.benchmarks && (
              <div className="col-span-full glass-card rounded-xl p-5 text-center text-slate-500">
                No benchmark data available
              </div>
            )}
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
                ? "Loading listings..."
                : data
                  ? `${data.count} listing${data.count !== 1 ? "s" : ""} found`
                  : ""}
            </p>
            <div className="flex items-center gap-2">
              {mineral && <Badge variant="gold">{mineral}</Badge>}
              {country && <Badge variant="info">{country}</Badge>}
            </div>
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
                        Property
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Location
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Country
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Mineral
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Stage
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Hectares
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Asking Price
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        $/Hectare
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Type
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading &&
                      Array.from({ length: 8 }).map((_, i) => (
                        <SkeletonRow key={i} />
                      ))}

                    {!loading &&
                      data?.listings?.map((row) => (
                        <tr
                          key={row.id}
                          className="border-b border-slate-700/50 hover:bg-slate-800/40 transition-colors"
                        >
                          {/* Property title */}
                          <td className="px-4 py-3">
                            <Link
                              href={`/properties/${row.slug}`}
                              className="text-gold-400 hover:text-gold-300 font-medium transition-colors"
                            >
                              {row.title}
                            </Link>
                          </td>

                          {/* Location */}
                          <td className="px-4 py-3 text-slate-300">
                            {row.location || "--"}
                          </td>

                          {/* Country */}
                          <td className="px-4 py-3 text-slate-300">
                            {row.country || "--"}
                          </td>

                          {/* Mineral */}
                          <td className="px-4 py-3">
                            <Badge variant="gold">
                              {row.primary_mineral || "--"}
                            </Badge>
                          </td>

                          {/* Stage */}
                          <td className="px-4 py-3">
                            <Badge
                              variant={
                                row.exploration_stage
                                  ?.toLowerCase()
                                  .includes("produc")
                                  ? "success"
                                  : row.exploration_stage
                                        ?.toLowerCase()
                                        .includes("feasib")
                                    ? "info"
                                    : "slate"
                              }
                            >
                              {row.exploration_stage || "--"}
                            </Badge>
                          </td>

                          {/* Hectares */}
                          <td className="px-4 py-3 text-right text-slate-300 font-mono">
                            {formatHectares(row.total_hectares)}
                          </td>

                          {/* Asking Price */}
                          <td className="px-4 py-3 text-right text-slate-200 font-mono">
                            {formatPrice(row.asking_price)}
                            {row.price_currency &&
                              row.price_currency !== "USD" && (
                                <span className="text-xs text-slate-500 ml-1">
                                  {row.price_currency}
                                </span>
                              )}
                          </td>

                          {/* $/Hectare - color-coded */}
                          <td
                            className={`px-4 py-3 text-right font-mono ${priceColorClass(row.price_per_hectare ?? 0, median)}`}
                          >
                            {formatPricePerHa(row.price_per_hectare)}
                          </td>

                          {/* Listing Type */}
                          <td className="px-4 py-3">
                            <Badge variant="slate">
                              {row.listing_type || "--"}
                            </Badge>
                          </td>
                        </tr>
                      ))}

                    {!loading && data?.listings?.length === 0 && (
                      <tr>
                        <td
                          colSpan={9}
                          className="px-4 py-12 text-center text-slate-500"
                        >
                          <div className="flex flex-col items-center gap-3">
                            <svg
                              className="w-10 h-10 text-slate-600"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                              />
                            </svg>
                            <p>
                              No listings found. Try adjusting your filters.
                            </p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Legend */}
          {!loading && data && data.listings.length > 0 && (
            <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                Below median (good value)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                Above median
              </span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
