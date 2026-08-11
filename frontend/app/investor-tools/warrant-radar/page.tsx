"use client";

import { Fragment, useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface Tranche {
  financing_id: number;
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  financing_type: string;
  announced_date: string;
  expiry_date: string;
  days_to_expiry: number;
  strike_price: number;
  current_price: number | null;
  price_currency: string | null;
  in_the_money: boolean;
  pct_to_strike: number | null;
  units_issued: number;
  est_warrants: number;
  est_proceeds: number;
  est_dilution_pct: number | null;
}

interface CompanyRow {
  company_id: number;
  company_name: string;
  ticker: string;
  exchange: string;
  current_price: number | null;
  price_currency: string | null;
  tranches: number;
  in_the_money_tranches: number;
  est_warrants: number;
  est_proceeds_if_all_exercised: number;
  est_proceeds_in_the_money: number;
  est_dilution_pct: number | null;
  next_expiry: string;
  lowest_strike: number;
  highest_strike: number;
  fully_funded_price: number;
  pct_to_fully_funded: number | null;
}

interface WallBucket {
  quarter: string;
  tranches: number;
  companies: number;
  est_warrants: number;
  est_proceeds: number;
  in_the_money: number;
}

interface RadarData {
  summary: {
    live_tranches: number;
    companies: number;
    est_warrants: number;
    in_the_money_tranches: number;
    out_of_money_tranches: number;
    est_proceeds_if_all_exercised: number;
    est_proceeds_in_the_money: number;
    next_expiry: string | null;
    excluded_implausible: number;
  };
  expiry_wall: WallBucket[];
  companies: CompanyRow[];
  tranches: Tranche[];
  tranches_truncated: boolean;
  assumptions: {
    warrant_coverage: number;
    warrants: string;
    currency: string;
    excluded: string;
  };
}

/* ---------- helpers ---------- */

function fmtMoney(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(2)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${Math.round(v).toLocaleString()}`;
}

function fmtCount(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(2)}B`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return v.toLocaleString();
}

function fmtPrice(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `$${v.toFixed(v < 1 ? 3 : 2)}`;
}

function fmtDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function toCSV(rows: CompanyRow[]): string {
  const head = [
    "Company",
    "Ticker",
    "Price",
    "Tranches",
    "In the money",
    "Est warrants",
    "Est proceeds if all exercised",
    "Est proceeds in the money",
    "Est dilution %",
    "Lowest strike",
    "Fully funded price",
    "% to fully funded",
    "Next expiry",
  ];
  const body = rows.map((r) =>
    [
      `"${r.company_name.replace(/"/g, '""')}"`,
      r.ticker,
      r.current_price ?? "",
      r.tranches,
      r.in_the_money_tranches,
      r.est_warrants,
      r.est_proceeds_if_all_exercised,
      r.est_proceeds_in_the_money,
      r.est_dilution_pct ?? "",
      r.lowest_strike,
      r.fully_funded_price,
      r.pct_to_fully_funded ?? "",
      r.next_expiry,
    ].join(","),
  );
  return [head.join(","), ...body].join("\n");
}

/* ---------- page ---------- */

export default function WarrantRadarPage() {
  const [data, setData] = useState<RadarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coverage, setCoverage] = useState("0.5");
  const [search, setSearch] = useState("");
  const [onlyITM, setOnlyITM] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    toolsAPI
      .warrantRadar({ coverage })
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e?.message || "Could not load warrant data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [coverage]);

  const companies = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return data.companies.filter((c) => {
      if (onlyITM && c.in_the_money_tranches === 0) return false;
      if (!q) return true;
      return (
        c.company_name.toLowerCase().includes(q) ||
        (c.ticker || "").toLowerCase().includes(q)
      );
    });
  }, [data, search, onlyITM]);

  const maxWallProceeds = useMemo(
    () => Math.max(1, ...(data?.expiry_wall || []).map((w) => w.est_proceeds)),
    [data],
  );

  const downloadCSV = () => {
    const blob = new Blob([toCSV(companies)], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `warrant-overhang-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const s = data?.summary;

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
              <Link href="/companies">
                <Button variant="ghost" size="sm">
                  Companies
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-10 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto">
          <Badge variant="gold" className="mb-3">
            Capital Structure
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-3">
            Warrant Overhang Radar
          </h1>
          <p className="text-slate-300 max-w-3xl">
            Every live warrant tranche issued in the placements we track — what
            the stock must reach before they are exercisable, how much cash
            reaches treasury when they are, and how many shares hit the market.
          </p>
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto">
          {loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Loading warrant book…
            </div>
          )}

          {error && !loading && (
            <div className="glass-card rounded-xl p-6 border-red-500/30">
              <p className="text-red-300 font-medium mb-1">
                Could not load warrant data
              </p>
              <p className="text-sm text-slate-400">{error}</p>
            </div>
          )}

          {data && !loading && (
            <>
              {/* Summary tiles */}
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                <Tile
                  label="Live tranches"
                  value={s!.live_tranches.toLocaleString()}
                  sub={`${s!.companies} companies`}
                />
                <Tile
                  label="Est. warrants outstanding"
                  value={fmtCount(s!.est_warrants)}
                  sub={`at ${data.assumptions.warrant_coverage} per unit`}
                />
                <Tile
                  label="Treasury if all exercised"
                  value={fmtMoney(s!.est_proceeds_if_all_exercised)}
                  sub="native currency"
                />
                <Tile
                  label="Exercisable today"
                  value={fmtMoney(s!.est_proceeds_in_the_money)}
                  sub={`${s!.in_the_money_tranches} tranches in the money`}
                  accent
                />
                <Tile
                  label="Next expiry"
                  value={s!.next_expiry ? fmtDate(s!.next_expiry) : "—"}
                  sub={`${s!.out_of_money_tranches} tranches out of the money`}
                />
              </div>

              {/* Expiry wall */}
              <div className="glass-card rounded-xl p-5 mb-6">
                <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
                  <h2 className="text-lg font-semibold text-slate-200">
                    Expiry wall
                  </h2>
                  <p className="text-xs text-slate-500">
                    When the overhang comes due, by quarter
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <div className="flex items-end gap-2 min-w-[560px] h-40">
                    {data.expiry_wall.map((w) => (
                      <div
                        key={w.quarter}
                        className="flex-1 flex flex-col items-center justify-end gap-2 group"
                        title={`${w.quarter}: ${w.tranches} tranches across ${w.companies} companies, ${fmtMoney(w.est_proceeds)}`}
                      >
                        <span className="text-[10px] text-slate-400 tabular-nums">
                          {fmtMoney(w.est_proceeds)}
                        </span>
                        <div
                          className="w-full rounded-t bg-gold-500/40 group-hover:bg-gold-400/70 transition-colors"
                          style={{
                            height: `${Math.max(4, (w.est_proceeds / maxWallProceeds) * 100)}%`,
                          }}
                        />
                        <span className="text-[10px] text-slate-500 whitespace-nowrap">
                          {w.quarter}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Controls */}
              <div className="glass-card rounded-xl p-4 mb-6 flex flex-wrap items-end gap-4">
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-xs text-slate-400 mb-1">
                    Search company or ticker
                  </label>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="e.g. Athena, AAG"
                    className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-gold-500/50"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Warrants per unit
                  </label>
                  <select
                    value={coverage}
                    onChange={(e) => setCoverage(e.target.value)}
                    className="bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-gold-500/50"
                  >
                    <option value="1">1 full warrant</option>
                    <option value="0.75">3/4 warrant</option>
                    <option value="0.5">1/2 warrant (typical)</option>
                    <option value="0.25">1/4 warrant</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-300 pb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onlyITM}
                    onChange={(e) => setOnlyITM(e.target.checked)}
                    className="accent-gold-500"
                  />
                  In the money only
                </label>
                <Button variant="ghost" size="sm" onClick={downloadCSV}>
                  Export CSV
                </Button>
              </div>

              {/* Company table */}
              <div className="glass-card rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[900px]">
                    <thead>
                      <tr className="border-b border-slate-700/60 text-[11px] uppercase tracking-wider text-slate-500">
                        <th className="text-left px-4 py-3">Company</th>
                        <th className="text-right px-3 py-3">Price</th>
                        <th className="text-right px-3 py-3">
                          Fully funded at
                        </th>
                        <th className="text-right px-3 py-3">Move needed</th>
                        <th className="text-right px-3 py-3">Est. warrants</th>
                        <th className="text-right px-3 py-3">
                          Treasury if exercised
                        </th>
                        <th className="text-right px-3 py-3">Dilution</th>
                        <th className="text-right px-4 py-3">Next expiry</th>
                      </tr>
                    </thead>
                    <tbody>
                      {companies.map((c) => {
                        const isOpen = expanded === c.company_id;
                        const tranches = data.tranches.filter(
                          (t) => t.company_id === c.company_id,
                        );
                        return (
                          <Fragment key={c.company_id}>
                            <tr
                              onClick={() =>
                                setExpanded(isOpen ? null : c.company_id)
                              }
                              className="border-b border-slate-800/60 hover:bg-slate-800/30 cursor-pointer"
                            >
                              <td className="px-4 py-3">
                                <div className="font-medium text-slate-200">
                                  {c.company_name}
                                </div>
                                <div className="text-xs text-slate-500">
                                  {c.ticker}
                                  {c.in_the_money_tranches > 0 && (
                                    <span className="ml-2 text-emerald-400">
                                      {c.in_the_money_tranches} in the money
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                                {fmtPrice(c.current_price)}
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                                {fmtPrice(c.fully_funded_price)}
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums">
                                {c.pct_to_fully_funded === null ? (
                                  <span className="text-slate-600">—</span>
                                ) : c.pct_to_fully_funded <= 0 ? (
                                  <span className="text-emerald-400">
                                    fully funded
                                  </span>
                                ) : (
                                  <span
                                    className={
                                      c.pct_to_fully_funded < 50
                                        ? "text-amber-300"
                                        : "text-slate-400"
                                    }
                                  >
                                    +{c.pct_to_fully_funded.toFixed(0)}%
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums text-slate-300">
                                {fmtCount(c.est_warrants)}
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums text-slate-200">
                                {fmtMoney(c.est_proceeds_if_all_exercised)}
                              </td>
                              <td className="px-3 py-3 text-right tabular-nums text-slate-400">
                                {c.est_dilution_pct === null
                                  ? "—"
                                  : `${c.est_dilution_pct.toFixed(1)}%`}
                              </td>
                              <td className="px-4 py-3 text-right text-slate-400 whitespace-nowrap">
                                {fmtDate(c.next_expiry)}
                              </td>
                            </tr>

                            {isOpen && (
                              <tr
                                key={`${c.company_id}-detail`}
                                className="bg-slate-900/60"
                              >
                                <td colSpan={8} className="px-4 py-4">
                                  <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                                    Warrant book — {tranches.length} tranche
                                    {tranches.length === 1 ? "" : "s"}
                                  </div>
                                  <div className="overflow-x-auto">
                                    <table className="w-full text-xs min-w-[720px]">
                                      <thead>
                                        <tr className="text-slate-500 border-b border-slate-800">
                                          <th className="text-left py-2 pr-3">
                                            Raised
                                          </th>
                                          <th className="text-left py-2 pr-3">
                                            Type
                                          </th>
                                          <th className="text-right py-2 pr-3">
                                            Strike
                                          </th>
                                          <th className="text-right py-2 pr-3">
                                            Units
                                          </th>
                                          <th className="text-right py-2 pr-3">
                                            Est. warrants
                                          </th>
                                          <th className="text-right py-2 pr-3">
                                            Proceeds
                                          </th>
                                          <th className="text-right py-2 pr-3">
                                            Status
                                          </th>
                                          <th className="text-right py-2">
                                            Expires
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {tranches.map((t) => (
                                          <tr
                                            key={t.financing_id}
                                            className="border-b border-slate-800/50"
                                          >
                                            <td className="py-2 pr-3 text-slate-400">
                                              {fmtDate(t.announced_date)}
                                            </td>
                                            <td className="py-2 pr-3 text-slate-400">
                                              {t.financing_type.replace(
                                                /_/g,
                                                " ",
                                              )}
                                            </td>
                                            <td className="py-2 pr-3 text-right tabular-nums text-slate-300">
                                              {fmtPrice(t.strike_price)}
                                            </td>
                                            <td className="py-2 pr-3 text-right tabular-nums text-slate-400">
                                              {fmtCount(t.units_issued)}
                                            </td>
                                            <td className="py-2 pr-3 text-right tabular-nums text-slate-400">
                                              {fmtCount(t.est_warrants)}
                                            </td>
                                            <td className="py-2 pr-3 text-right tabular-nums text-slate-300">
                                              {fmtMoney(t.est_proceeds)}
                                            </td>
                                            <td className="py-2 pr-3 text-right">
                                              {t.in_the_money ? (
                                                <span className="text-emerald-400">
                                                  in the money
                                                </span>
                                              ) : t.pct_to_strike === null ? (
                                                <span className="text-slate-600">
                                                  no price
                                                </span>
                                              ) : (
                                                <span className="text-slate-500">
                                                  +{t.pct_to_strike.toFixed(0)}%
                                                  needed
                                                </span>
                                              )}
                                            </td>
                                            <td className="py-2 text-right text-slate-400 whitespace-nowrap">
                                              {fmtDate(t.expiry_date)}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {companies.length === 0 && (
                  <div className="p-8 text-center text-slate-400 text-sm">
                    No companies match those filters.
                  </div>
                )}
              </div>

              {/* Assumptions — these numbers are estimates and should say so */}
              <div className="mt-6 glass-card rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">
                  How to read these numbers
                </h3>
                <ul className="text-xs text-slate-400 space-y-2 leading-relaxed">
                  <li>{data.assumptions.warrants}</li>
                  <li>{data.assumptions.currency}</li>
                  {data.summary.excluded_implausible > 0 && (
                    <li>{data.assumptions.excluded}</li>
                  )}
                  <li>
                    &ldquo;Fully funded at&rdquo; is the highest strike in a
                    company&rsquo;s live warrant book — the price at which every
                    outstanding warrant becomes exercisable, and the company
                    could be funded without another placement.
                  </li>
                </ul>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

/* ---------- small components ---------- */

function Tile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div className="glass-card rounded-xl p-4">
      <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
        {label}
      </div>
      <div
        className={`text-xl font-semibold tabular-nums ${accent ? "text-emerald-400" : "text-slate-200"}`}
      >
        {value}
      </div>
      {sub && <div className="text-[11px] text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}
