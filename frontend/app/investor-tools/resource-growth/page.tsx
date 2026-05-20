"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
}

interface ResourceCategory {
  category: string;
  tonnes: number;
  gold_grade_gpt: number | null;
  gold_ounces: number | null;
  silver_ounces: number | null;
}

interface TimelineEntry {
  report_date: string;
  standard: string;
  categories: ResourceCategory[];
  resource_gold_oz: number;
  reserve_gold_oz: number;
}

interface Growth {
  first_report: string;
  latest_report: string;
  first_oz: number;
  latest_oz: number;
  change_pct: number;
}

interface ProjectData {
  project_id: number;
  project_name: string;
  primary_commodity: string;
  estimate_count: number;
  timeline: TimelineEntry[];
  growth: Growth | null;
}

interface ResourceData {
  available_companies: AvailableCompany[];
  company?: { id: number; name: string; ticker: string };
  projects: ProjectData[];
}

/* ---------- helpers ---------- */

function fmtOz(v: number | null | undefined): string {
  if (!v) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return Math.round(v).toLocaleString();
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

/* ---------- page ---------- */

export default function ResourceGrowthPage() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AvailableCompany | null>(null);
  const [data, setData] = useState<ResourceData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.resourceGrowth({})) as ResourceData;
        setAvailable(res.available_companies || []);
      } catch {
        setError("Failed to load the company list. Please refresh.");
      } finally {
        setInitialLoading(false);
      }
    })();
  }, []);

  const searchMatches = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return available
      .filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.ticker || "").toLowerCase().includes(q),
      )
      .slice(0, 8);
  }, [search, available]);

  const selectCompany = async (c: AvailableCompany) => {
    setSelected(c);
    setSearch("");
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = (await toolsAPI.resourceGrowth({
        company_id: String(c.id),
      })) as ResourceData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to load resource history.");
    } finally {
      setLoading(false);
    }
  };

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
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-3">
            Resource Analysis
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-3">
            Resource Growth Tracker
          </h1>
          <p className="text-slate-300 max-w-xl mx-auto">
            See how a company&apos;s mineral resource estimates have evolved
            across successive NI 43-101 reports — contained ounces, grade and
            tonnage over time.
          </p>
        </div>
      </section>

      {/* Company picker */}
      <section className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-5 sm:p-6">
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2">
              Company
            </label>
            {selected ? (
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/30 text-sm text-gold-300">
                  {selected.name}
                  {selected.ticker && (
                    <span className="text-gold-400/60">{selected.ticker}</span>
                  )}
                </span>
                <button
                  onClick={() => {
                    setSelected(null);
                    setData(null);
                  }}
                  className="text-sm text-slate-400 hover:text-gold-400"
                >
                  Change
                </button>
              </div>
            ) : (
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={
                    initialLoading
                      ? "Loading companies…"
                      : "Search a company by name or ticker…"
                  }
                  disabled={initialLoading}
                  className="w-full bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-3 py-2 focus:border-gold-500/50 focus:outline-none disabled:opacity-50"
                />
                {searchMatches.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-slate-800 border border-slate-700 rounded-md shadow-xl max-h-64 overflow-y-auto">
                    {searchMatches.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => selectCompany(c)}
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
                {!initialLoading && (
                  <p className="text-xs text-slate-500 mt-2">
                    {available.length} companies have resource estimates on
                    record.
                  </p>
                )}
              </div>
            )}
            {error && <p className="text-sm text-red-400 mt-3">{error}</p>}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto space-y-8">
          {loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Loading resource history…
            </div>
          )}

          {!loading && data && data.projects.length === 0 && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              No resource estimates are on record for{" "}
              {data.company?.name || "this company"} yet.
            </div>
          )}

          {!loading &&
            data &&
            data.projects.map((project) => {
              const maxOz = Math.max(
                ...project.timeline.map((t) => t.resource_gold_oz),
                1,
              );
              return (
                <div
                  key={project.project_id}
                  className="glass-card rounded-xl p-6"
                >
                  {/* Project header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-slate-100">
                        {project.project_name}
                      </h2>
                      <Badge variant="slate" className="capitalize">
                        {project.primary_commodity.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    {project.growth && (
                      <div className="text-sm text-slate-400">
                        <span
                          className={
                            project.growth.change_pct >= 0
                              ? "text-emerald-400 font-semibold"
                              : "text-red-400 font-semibold"
                          }
                        >
                          {project.growth.change_pct >= 0 ? "+" : ""}
                          {project.growth.change_pct}%
                        </span>{" "}
                        contained gold ({fmtOz(project.growth.first_oz)} →{" "}
                        {fmtOz(project.growth.latest_oz)} oz)
                      </div>
                    )}
                  </div>

                  {/* Bar chart: resource gold oz per report */}
                  <div className="flex items-end gap-3 h-48 mb-6">
                    {project.timeline.map((t) => {
                      const pct = (t.resource_gold_oz / maxOz) * 100;
                      return (
                        <div
                          key={t.report_date}
                          className="flex-1 flex flex-col items-center gap-1 min-w-0"
                        >
                          <span className="text-[10px] text-slate-400">
                            {fmtOz(t.resource_gold_oz)} oz
                          </span>
                          <div
                            className="w-full flex justify-center"
                            style={{ height: "150px" }}
                          >
                            <div
                              className="w-full max-w-[64px] rounded-t bg-gradient-to-t from-gold-600 to-gold-400 self-end transition-all duration-500"
                              style={{ height: `${Math.max(pct, 2)}%` }}
                              title={`${fmtOz(t.resource_gold_oz)} oz contained gold`}
                            />
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {fmtDate(t.report_date)}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Timeline table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                          <th className="text-left pb-2 pr-4">Report Date</th>
                          <th className="text-left pb-2 pr-4">Category</th>
                          <th className="text-right pb-2 pr-4">Tonnes</th>
                          <th className="text-right pb-2 pr-4">Grade (g/t)</th>
                          <th className="text-right pb-2 pr-4">Gold (oz)</th>
                          <th className="text-right pb-2">Silver (oz)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {project.timeline.flatMap((t) =>
                          t.categories.map((c, ci) => (
                            <tr
                              key={`${t.report_date}-${ci}`}
                              className="border-b border-slate-800/40"
                            >
                              <td className="py-2 pr-4 text-slate-400">
                                {ci === 0 ? (
                                  <>
                                    {new Date(t.report_date).toLocaleDateString(
                                      "en-US",
                                      {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      },
                                    )}
                                    <span className="block text-[10px] text-slate-600">
                                      {t.standard}
                                    </span>
                                  </>
                                ) : (
                                  ""
                                )}
                              </td>
                              <td className="py-2 pr-4 text-slate-300">
                                {c.category}
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-400">
                                {c.tonnes
                                  ? Math.round(c.tonnes).toLocaleString()
                                  : "—"}
                              </td>
                              <td className="py-2 pr-4 text-right text-slate-400">
                                {c.gold_grade_gpt != null
                                  ? c.gold_grade_gpt.toFixed(2)
                                  : "—"}
                              </td>
                              <td className="py-2 pr-4 text-right text-gold-400">
                                {fmtOz(c.gold_ounces)}
                              </td>
                              <td className="py-2 text-right text-slate-400">
                                {fmtOz(c.silver_ounces)}
                              </td>
                            </tr>
                          )),
                        )}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-slate-500 mt-3">
                    Bars show contained gold from Inferred + Indicated +
                    Measured categories. Measured &amp; Indicated (combined) and
                    reserve categories are shown in the table but excluded from
                    the bar total to avoid double-counting.
                  </p>
                </div>
              );
            })}

          {!loading && !data && !error && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Search and select a company above to see its resource history.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
