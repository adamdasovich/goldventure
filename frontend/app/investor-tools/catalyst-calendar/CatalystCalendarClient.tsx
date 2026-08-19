"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Release {
  id: number;
  title: string;
  date: string;
  url: string;
}

interface CompanyActivity {
  company_id: number;
  company_name: string;
  ticker: string;
  releases: Release[];
  count: number;
  latest_date: string;
  days_since_last: number;
  avg_days_between: number;
}

interface WeeklyVolume {
  week: string;
  count: number;
}

interface CatalystCalendarData {
  companies: CompanyActivity[];
  quiet_companies: CompanyActivity[];
  weekly_volume: WeeklyVolume[];
  total_releases: number;
  period_days: number;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const DAYS_OPTIONS = [30, 60, 90, 180] as const;
type DaysOption = (typeof DAYS_OPTIONS)[number];

const COMMODITY_OPTIONS = [
  { value: "", label: "All Commodities" },
  { value: "gold", label: "Gold" },
  { value: "silver", label: "Silver" },
  { value: "copper", label: "Copper" },
  { value: "lithium", label: "Lithium" },
  { value: "uranium", label: "Uranium" },
  { value: "nickel", label: "Nickel" },
  { value: "zinc", label: "Zinc" },
  { value: "platinum", label: "Platinum" },
];

type SortMode = "most_active" | "most_quiet" | "alphabetical";

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatDate(iso: string): string {
  if (!iso) return "N/A";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function sortCompanies(
  companies: CompanyActivity[],
  mode: SortMode,
): CompanyActivity[] {
  const copy = [...companies];
  switch (mode) {
    case "most_active":
      return copy.sort((a, b) => b.count - a.count);
    case "most_quiet":
      return copy.sort((a, b) => b.days_since_last - a.days_since_last);
    case "alphabetical":
      return copy.sort((a, b) => a.company_name.localeCompare(b.company_name));
    default:
      return copy;
  }
}

/* ------------------------------------------------------------------ */
/*  Skeleton                                                           */
/* ------------------------------------------------------------------ */

function Skeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
      {/* filter bar */}
      <div className="flex gap-3 justify-center">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-9 w-16 bg-slate-700/50 rounded-lg" />
        ))}
        <div className="h-9 w-40 bg-slate-700/50 rounded-lg" />
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-5 h-24" />
        ))}
      </div>

      {/* chart */}
      <div className="glass-card rounded-xl p-5 h-52" />

      {/* quiet alert */}
      <div className="glass-card rounded-xl p-5 h-28" />

      {/* table */}
      <div className="glass-card rounded-xl p-5 h-96" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Bar Chart (CSS-only)                                               */
/* ------------------------------------------------------------------ */

function WeeklyBarChart({ data }: { data: WeeklyVolume[] }) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="flex items-end gap-1.5 h-40">
      {data.map((week, i) => {
        const heightPct = (week.count / maxCount) * 100;
        const label = new Date(week.week).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });
        return (
          <div
            key={i}
            className="flex-1 flex flex-col items-center justify-end h-full group relative"
          >
            {/* tooltip */}
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 border border-slate-700 text-xs text-slate-200 px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {week.count} releases
            </div>
            <div
              className="w-full rounded-t bg-gradient-to-t from-gold-500 to-gold-400 transition-all duration-300 group-hover:from-gold-400 group-hover:to-gold-300"
              style={{
                height: `${Math.max(heightPct, 2)}%`,
                minHeight: "2px",
              }}
            />
            <span className="text-[9px] text-slate-500 mt-1.5 truncate w-full text-center">
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Expandable Releases                                                */
/* ------------------------------------------------------------------ */

function ExpandableReleases({ releases }: { releases: Release[] }) {
  const [expanded, setExpanded] = useState(false);
  const shown = expanded ? releases.slice(0, 5) : releases.slice(0, 0);
  const previewCount = Math.min(releases.length, 5);

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-gold-400 hover:text-gold-300 transition-colors flex items-center gap-1"
      >
        {expanded ? "Hide" : `Show ${previewCount}`} recent release
        {previewCount !== 1 ? "s" : ""}
        <span
          className={`inline-block transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          &#9660;
        </span>
      </button>
      {expanded && (
        <ul className="mt-2 space-y-1.5 pl-2 border-l border-slate-700/50">
          {shown.map((r) => (
            <li key={r.id} className="text-xs">
              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-300 hover:text-gold-400 transition-colors line-clamp-1"
                title={r.title}
              >
                {r.title}
              </a>
              <span className="text-slate-600 ml-1.5">
                {formatDate(r.date)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function CatalystCalendarClient() {
  const [data, setData] = useState<CatalystCalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [days, setDays] = useState<DaysOption>(60);
  const [commodity, setCommodity] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("most_active");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { days: String(days) };
      if (commodity) params.commodity = commodity;
      const res = await toolsAPI.catalystCalendar(params);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load catalyst calendar data");
    } finally {
      setLoading(false);
    }
  }, [days, commodity]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading)
    return (
      <>
        <Skeleton />
      </>
    );

  if (error || !data) {
    return (
      <>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 flex justify-center">
          <div className="glass-card rounded-xl p-8 text-center max-w-md">
            <p className="text-red-400 text-lg font-semibold mb-2">
              Unable to load Catalyst Calendar
            </p>
            <p className="text-slate-400 text-sm mb-4">{error}</p>
            <Button variant="secondary" size="sm" onClick={fetchData}>
              Retry
            </Button>
          </div>
        </div>
      </>
    );
  }

  const sortedCompanies = sortCompanies(data.companies, sortMode);
  const avgReleasesPerCompany =
    data.companies.length > 0
      ? (data.total_releases / data.companies.length).toFixed(1)
      : "0";

  return (
    <>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* ============================================================= */}
        {/*  Filters                                                       */}
        {/* ============================================================= */}
        <section className="flex flex-wrap items-center justify-center gap-3">
          {/* Days toggle */}
          <div className="flex rounded-lg overflow-hidden border border-slate-700">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  days === d
                    ? "bg-gold-500/20 text-gold-400 border-gold-500/30"
                    : "bg-slate-800/50 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>

          {/* Commodity dropdown */}
          <select
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            className="bg-slate-800/70 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-gold-500 transition-colors"
          >
            {COMMODITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </section>

        {/* ============================================================= */}
        {/*  Summary Stats                                                 */}
        {/* ============================================================= */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-card rounded-xl p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
              Period
            </p>
            <p className="text-2xl font-bold text-slate-100">
              {data.period_days}
              <span className="text-sm text-slate-500 ml-1">days</span>
            </p>
          </div>
          <div className="glass-card rounded-xl p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
              Total Releases
            </p>
            <p className="text-2xl font-bold text-gold-400">
              {data.total_releases}
            </p>
          </div>
          <div className="glass-card rounded-xl p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
              Companies Tracked
            </p>
            <p className="text-2xl font-bold text-slate-100">
              {data.companies.length}
            </p>
          </div>
          <div className="glass-card rounded-xl p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
              Avg per Company
            </p>
            <p className="text-2xl font-bold text-gold-400">
              {avgReleasesPerCompany}
            </p>
          </div>
        </section>

        {/* ============================================================= */}
        {/*  Weekly News Volume Bar Chart                                   */}
        {/* ============================================================= */}
        {data.weekly_volume.length > 0 && (
          <section>
            <div className="glass-card rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Weekly News Volume
              </h2>
              <WeeklyBarChart data={data.weekly_volume} />
            </div>
          </section>
        )}

        {/* ============================================================= */}
        {/*  Quiet Companies Alert                                         */}
        {/* ============================================================= */}
        {data.quiet_companies.length > 0 && (
          <section>
            <div className="glass-card rounded-xl p-5 border border-amber-500/20 bg-amber-500/5">
              <div className="flex items-start gap-3">
                <div className="shrink-0 mt-0.5">
                  <span className="text-amber-400 text-xl">&#9888;</span>
                </div>
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-2">
                    Quiet Companies — No News in 30+ Days
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {data.quiet_companies.map((c) => (
                      <Link
                        key={c.company_id}
                        href={`/companies/${c.company_id}`}
                        className="inline-flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg px-2.5 py-1.5 hover:bg-amber-500/20 transition-colors group"
                      >
                        <span className="text-sm text-amber-200 group-hover:text-amber-100 transition-colors">
                          {c.company_name}
                        </span>
                        <Badge variant="warning" className="text-[10px]">
                          {c.days_since_last}d silent
                        </Badge>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ============================================================= */}
        {/*  Company Activity Table                                        */}
        {/* ============================================================= */}
        <section>
          <div className="glass-card rounded-xl p-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-3">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                  Company Activity
                </h2>
                <ExportButton
                  filename="catalyst-calendar"
                  rows={data?.companies ?? []}
                  columns={[
                    { label: "Company", value: (c) => c.company_name },
                    { label: "Ticker", value: (c) => c.ticker },
                    { label: "Releases", value: (c) => c.count },
                    { label: "Latest release", value: (c) => c.latest_date },
                    {
                      label: "Days since last",
                      value: (c) => c.days_since_last,
                    },
                    {
                      label: "Avg days between",
                      value: (c) => c.avg_days_between,
                    },
                  ]}
                />
              </div>
              <div className="flex rounded-lg overflow-hidden border border-slate-700 text-xs">
                {(
                  [
                    { value: "most_active", label: "Most Active" },
                    { value: "most_quiet", label: "Most Quiet" },
                    { value: "alphabetical", label: "A-Z" },
                  ] as { value: SortMode; label: string }[]
                ).map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSortMode(opt.value)}
                    className={`px-3 py-1.5 font-medium transition-colors ${
                      sortMode === opt.value
                        ? "bg-gold-500/20 text-gold-400"
                        : "bg-slate-800/50 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                      Company
                    </th>
                    <th className="text-left py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider hidden sm:table-cell">
                      Ticker
                    </th>
                    <th className="text-center py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                      Releases
                    </th>
                    <th className="text-left py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider hidden md:table-cell">
                      Last Release
                    </th>
                    <th className="text-center py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                      Days Since
                    </th>
                    <th className="text-center py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider hidden lg:table-cell">
                      Avg Gap
                    </th>
                    <th className="text-left py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider hidden xl:table-cell">
                      Recent Releases
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {sortedCompanies.map((c) => {
                    const isQuiet = c.days_since_last >= 30;
                    return (
                      <tr
                        key={c.company_id}
                        className="hover:bg-slate-800/30 transition-colors"
                      >
                        {/* Company Name */}
                        <td className="py-3 px-2">
                          <Link
                            href={`/companies/${c.company_id}`}
                            className="text-slate-200 hover:text-gold-400 transition-colors font-medium"
                          >
                            {c.company_name}
                          </Link>
                        </td>

                        {/* Ticker */}
                        <td className="py-3 px-2 hidden sm:table-cell">
                          <span className="text-xs text-slate-500 font-mono">
                            {c.ticker}
                          </span>
                        </td>

                        {/* Release Count */}
                        <td className="py-3 px-2 text-center">
                          <span className="text-gold-400 font-semibold">
                            {c.count}
                          </span>
                        </td>

                        {/* Last Release Date */}
                        <td className="py-3 px-2 hidden md:table-cell">
                          <span className="text-slate-300 text-xs">
                            {formatDate(c.latest_date)}
                          </span>
                        </td>

                        {/* Days Since Last */}
                        <td className="py-3 px-2 text-center">
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                              isQuiet
                                ? "bg-amber-500/15 text-amber-400"
                                : c.days_since_last <= 7
                                  ? "bg-emerald-500/15 text-emerald-400"
                                  : "bg-slate-700/50 text-slate-300"
                            }`}
                          >
                            {c.days_since_last}d
                          </span>
                        </td>

                        {/* Avg Days Between */}
                        <td className="py-3 px-2 text-center hidden lg:table-cell">
                          <span className="text-slate-400 text-xs">
                            {c.avg_days_between > 0
                              ? `${c.avg_days_between.toFixed(0)}d`
                              : "--"}
                          </span>
                        </td>

                        {/* Expandable Releases */}
                        <td className="py-3 px-2 hidden xl:table-cell">
                          {c.releases && c.releases.length > 0 ? (
                            <ExpandableReleases releases={c.releases} />
                          ) : (
                            <span className="text-xs text-slate-600">
                              No releases
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {sortedCompanies.length === 0 && (
                    <tr>
                      <td
                        colSpan={7}
                        className="py-12 text-center text-slate-500"
                      >
                        No companies found for the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ============================================================= */}
        {/*  Footer                                                        */}
        {/* ============================================================= */}
        <footer className="pt-4 pb-8 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-600">
            Showing {data.period_days}-day window
            {commodity ? ` for ${commodity}` : ""} &middot;{" "}
            {data.total_releases} total releases across {data.companies.length}{" "}
            companies
          </p>
        </footer>
      </div>
    </>
  );
}
