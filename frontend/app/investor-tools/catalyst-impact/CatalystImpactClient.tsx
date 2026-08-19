"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Badge } from "@/components/ui/Badge";
import CompanyActions from "@/components/ui/CompanyActions";
import ExportButton from "@/components/ui/ExportButton";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
}

interface CatalystType {
  release_type: string;
  event_count: number;
  avg_1d: number | null;
  avg_5d: number | null;
  avg_20d: number | null;
  sample_1d: number;
  sample_5d: number;
  sample_20d: number;
}

interface CatalystEvent {
  date: string;
  title: string;
  release_type: string;
  url: string;
  change_1d: number | null;
  change_5d: number | null;
  change_20d: number | null;
}

interface CatalystData {
  available_companies: AvailableCompany[];
  company?: { id: number; name: string; ticker: string };
  window_days: number;
  total_events: number;
  by_catalyst_type: CatalystType[];
  events: CatalystEvent[];
  message?: string;
}

/* ---------- constants ---------- */

const DAYS_OPTIONS = [
  { label: "6M", value: 180 },
  { label: "1Y", value: 365 },
  { label: "2Y", value: 730 },
  { label: "3Y", value: 1095 },
] as const;

const HORIZONS = [
  { key: "1d", label: "+1 day" },
  { key: "5d", label: "+5 days" },
  { key: "20d", label: "+20 days" },
] as const;

/* ---------- helpers ---------- */

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function pctColor(v: number | null | undefined): string {
  if (v == null) return "text-slate-500";
  if (v > 0) return "text-emerald-400";
  if (v < 0) return "text-red-400";
  return "text-slate-300";
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/* ---------- diverging reaction bar ---------- */

function ReactionBar({
  value,
  maxAbs,
}: {
  value: number | null;
  maxAbs: number;
}) {
  if (value == null || maxAbs <= 0) {
    return <div className="h-2 rounded-full bg-slate-800/80" />;
  }
  const half = Math.min(Math.abs(value) / maxAbs, 1) * 50;
  const positive = value >= 0;
  return (
    <div className="relative h-2 rounded-full bg-slate-800/80">
      {/* center line */}
      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
      <div
        className={`absolute top-0 bottom-0 rounded-full ${
          positive ? "bg-emerald-500" : "bg-red-500"
        }`}
        style={
          positive
            ? { left: "50%", width: `${half}%` }
            : { right: "50%", width: `${half}%` }
        }
      />
    </div>
  );
}

/* ---------- page ---------- */

export default function CatalystImpactClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AvailableCompany | null>(null);
  const [days, setDays] = useState<number>(365);
  const [data, setData] = useState<CatalystData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.catalystImpact({})) as CatalystData;
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

  // Adopt ?company_id= so links from other tools land on the right company
  // instead of an empty picker. Read off window.location rather than
  // useSearchParams, which would force this prerendered page's client tree
  // into a Suspense boundary just to satisfy the build.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const requested = new URLSearchParams(window.location.search).get(
      "company_id",
    );
    if (!requested || selected || available.length === 0) return;
    const match = available.find((c) => String(c.id) === requested);
    if (match) setSelected(match);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [available, selected]);


  const runStudy = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const res = (await toolsAPI.catalystImpact({
        company_id: String(selected.id),
        days: String(days),
      })) as CatalystData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to run the catalyst study.");
    } finally {
      setLoading(false);
    }
  }, [selected, days]);

  useEffect(() => {
    if (selected) runStudy();
  }, [selected, days, runStudy]);

  // Largest absolute average reaction — scales every diverging bar.
  const maxAbs = useMemo(() => {
    if (!data?.by_catalyst_type?.length) return 1;
    const vals: number[] = [];
    data.by_catalyst_type.forEach((t) => {
      [t.avg_1d, t.avg_5d, t.avg_20d].forEach((v) => {
        if (v != null) vals.push(Math.abs(v));
      });
    });
    return Math.max(...vals, 1);
  }, [data]);

  return (
    <>
      {/* Controls */}
      <section className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-xl p-5 sm:p-6 space-y-5">
            {/* Company picker */}
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2">
                Company
              </label>
              {selected ? (
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-500/15 border border-gold-500/30 text-sm text-gold-300">
                    {selected.name}
                    {selected.ticker && (
                      <span className="text-gold-400/60">
                        {selected.ticker}
                      </span>
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
                          onClick={() => {
                            setSelected(c);
                            setSearch("");
                          }}
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
              )}
            </div>

            {selected && (
              <div className="border-t border-slate-700/40 pt-3">
                <CompanyActions
                  companyId={selected.id}
                  companyName={selected.name}
                  currentSlug="catalyst-impact"
                />
              </div>
            )}

            {/* Window */}
            <div className="flex items-center gap-1">
              <span className="text-xs text-slate-400 mr-1">News window:</span>
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

            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto space-y-8">
          {!selected && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Search and select a company above to study how its news moves the
              stock.
            </div>
          )}

          {selected && loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Running event study…
            </div>
          )}

          {selected && !loading && data && data.message && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              {data.message}
            </div>
          )}

          {selected &&
            !loading &&
            data &&
            !data.message &&
            data.by_catalyst_type.length === 0 && (
              <div className="glass-card rounded-xl p-10 text-center text-slate-400">
                No news releases found for {data.company?.name} in this window.
                Try a longer window.
              </div>
            )}

          {selected &&
            !loading &&
            data &&
            !data.message &&
            data.by_catalyst_type.length > 0 && (
              <>
                {/* By catalyst type */}
                <div className="glass-card rounded-xl p-6">
                  <h2 className="text-sm font-semibold text-gold-400 mb-1">
                    Average Price Reaction by Catalyst Type
                  </h2>
                  <p className="text-xs text-slate-500 mb-5">
                    Based on {data.total_events} news releases over the last{" "}
                    {data.window_days} days.
                  </p>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {data.by_catalyst_type.map((t) => (
                      <div
                        key={t.release_type}
                        className="rounded-lg bg-slate-800/40 border border-slate-700/40 p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-slate-200">
                            {t.release_type}
                          </span>
                          <Badge variant="slate">
                            {t.event_count}{" "}
                            {t.event_count === 1 ? "event" : "events"}
                          </Badge>
                        </div>
                        <div className="space-y-2.5">
                          {HORIZONS.map((h) => {
                            const avg = t[
                              `avg_${h.key}` as keyof CatalystType
                            ] as number | null;
                            const sample = t[
                              `sample_${h.key}` as keyof CatalystType
                            ] as number;
                            return (
                              <div
                                key={h.key}
                                className="flex items-center gap-3"
                              >
                                <span className="text-xs text-slate-500 w-16 shrink-0">
                                  {h.label}
                                </span>
                                <div className="flex-1">
                                  <ReactionBar value={avg} maxAbs={maxAbs} />
                                </div>
                                <span
                                  className={`text-sm font-semibold w-20 text-right shrink-0 ${pctColor(
                                    avg,
                                  )}`}
                                >
                                  {fmtPct(avg)}
                                </span>
                                <span className="text-[10px] text-slate-600 w-8 shrink-0">
                                  n={sample}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-4">
                    Each bar is the average % share-price change measured 1, 5
                    and 20 trading days after a release of that type. Small
                    samples (n &lt; 4) are weak evidence — treat as directional
                    only.
                  </p>
                </div>

                {/* Event-level table */}
                {data.events.length > 0 && (
                  <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between gap-3 mb-4">
                      <h2 className="text-sm font-semibold text-gold-400">
                        Individual News Events
                      </h2>
                      <ExportButton
                        filename={`catalyst-impact-${data.company?.ticker || "company"}`}
                        rows={data.events}
                        columns={[
                          { label: "Date", value: (e) => e.date },
                          { label: "Type", value: (e) => e.release_type },
                          { label: "Headline", value: (e) => e.title },
                          { label: "1d change %", value: (e) => e.change_1d },
                          { label: "5d change %", value: (e) => e.change_5d },
                          { label: "20d change %", value: (e) => e.change_20d },
                          { label: "URL", value: (e) => e.url },
                        ]}
                      />
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                            <th className="text-left pb-2 pr-4">Date</th>
                            <th className="text-left pb-2 pr-4">Release</th>
                            <th className="text-left pb-2 pr-4">Type</th>
                            <th className="text-right pb-2 pr-4">+1d</th>
                            <th className="text-right pb-2 pr-4">+5d</th>
                            <th className="text-right pb-2">+20d</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.events.map((ev, i) => (
                            <tr
                              key={i}
                              className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                            >
                              <td className="py-2 pr-4 text-slate-400 whitespace-nowrap">
                                {fmtDate(ev.date)}
                              </td>
                              <td className="py-2 pr-4 text-slate-300 max-w-md">
                                {ev.url ? (
                                  <a
                                    href={ev.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-gold-400"
                                  >
                                    {ev.title}
                                  </a>
                                ) : (
                                  ev.title
                                )}
                              </td>
                              <td className="py-2 pr-4">
                                <Badge variant="slate">{ev.release_type}</Badge>
                              </td>
                              <td
                                className={`py-2 pr-4 text-right ${pctColor(
                                  ev.change_1d,
                                )}`}
                              >
                                {fmtPct(ev.change_1d)}
                              </td>
                              <td
                                className={`py-2 pr-4 text-right ${pctColor(
                                  ev.change_5d,
                                )}`}
                              >
                                {fmtPct(ev.change_5d)}
                              </td>
                              <td
                                className={`py-2 text-right ${pctColor(
                                  ev.change_20d,
                                )}`}
                              >
                                {fmtPct(ev.change_20d)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
        </div>
      </section>
    </>
  );
}
