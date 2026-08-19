"use client";

import { useState, useEffect, useMemo } from "react";
import { toolsAPI } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import CompanyActions from "@/components/ui/CompanyActions";
import ExportButton from "@/components/ui/ExportButton";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
}

interface FinancingRow {
  id: number;
  announced_date: string;
  financing_type: string;
  status: string;
  amount_raised_usd: number;
  shares_issued: number | null;
  cumulative_shares: number;
  price_per_share: number | null;
  has_warrants: boolean;
  warrant_strike_price: number | null;
  warrant_expiry_date: string | null;
  warrant_active: boolean;
}

interface DilutionSummary {
  current_shares_outstanding: number | null;
  financing_count: number;
  total_shares_issued: number | null;
  total_capital_raised_usd: number;
  issued_shares_pct_of_current: number | null;
  active_warrant_tranches: number;
}

interface DilutionData {
  available_companies: AvailableCompany[];
  company?: { id: number; name: string; ticker: string };
  summary?: DilutionSummary;
  financings: FinancingRow[];
}

/* ---------- helpers ---------- */

/**
 * Financing amounts are stored in the deal's own currency (usually CAD) under a
 * field named amount_raised_usd. Render them as plain dollars rather than
 * asserting USD.
 */
function fmtMoney(v: number): string {
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${Math.round(v).toLocaleString()}`;
}

function fmtShares(v: number | null | undefined): string {
  if (!v) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return Math.round(v).toLocaleString();
}

function fmtType(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/* ---------- page ---------- */

export default function DilutionTrackerClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AvailableCompany | null>(null);
  const [data, setData] = useState<DilutionData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.dilutionTracker({})) as DilutionData;
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
  // instead of an empty picker. Read straight off window.location rather than
  // useSearchParams: this page is statically prerendered, and that hook forces
  // the whole client tree into a Suspense boundary to satisfy the build.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const requested = new URLSearchParams(window.location.search).get(
      "company_id",
    );
    if (!requested || selected || available.length === 0) return;
    const match = available.find((c) => String(c.id) === requested);
    if (match) selectCompany(match);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [available, selected]);

  const selectCompany = async (c: AvailableCompany) => {
    setSelected(c);
    setSearch("");
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = (await toolsAPI.dilutionTracker({
        company_id: String(c.id),
      })) as DilutionData;
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to load dilution history.");
    } finally {
      setLoading(false);
    }
  };

  const maxCumulative = useMemo(() => {
    if (!data?.financings?.length) return 1;
    return Math.max(...data.financings.map((f) => f.cumulative_shares), 1);
  }, [data]);

  return (
    <>
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
                    {available.length} companies have financing records.
                  </p>
                )}
              </div>
            )}
            {selected && (
              <div className="mt-4 border-t border-slate-700/40 pt-3">
                <CompanyActions
                  companyId={selected.id}
                  companyName={selected.name}
                  currentSlug="dilution-tracker"
                />
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
              Loading dilution history…
            </div>
          )}

          {!loading && data && data.financings.length === 0 && data.company && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              No financing records are on file for {data.company.name}.
            </div>
          )}

          {!loading && data && data.summary && data.financings.length > 0 && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Financings
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {data.summary.financing_count}
                  </p>
                </div>
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Total Raised
                  </p>
                  <p className="text-2xl font-bold text-gold-400">
                    {fmtMoney(data.summary.total_capital_raised_usd)}
                  </p>
                </div>
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Issued vs Float
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {data.summary.issued_shares_pct_of_current != null
                      ? `${data.summary.issued_shares_pct_of_current}%`
                      : "—"}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    of current shares outstanding
                  </p>
                </div>
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Active Warrants
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {data.summary.active_warrant_tranches}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    tranches not yet expired
                  </p>
                </div>
              </div>

              {/* Cumulative dilution chart */}
              <div className="glass-card rounded-xl p-6">
                <h2 className="text-sm font-semibold text-gold-400 mb-4">
                  Cumulative Shares Issued via Financings
                </h2>
                <div className="flex items-end gap-2 h-48">
                  {data.financings.map((f) => {
                    const pct = (f.cumulative_shares / maxCumulative) * 100;
                    return (
                      <div
                        key={f.id}
                        className="flex-1 flex flex-col items-center gap-1 min-w-0"
                      >
                        <span className="text-[10px] text-slate-400">
                          {fmtShares(f.cumulative_shares)}
                        </span>
                        <div
                          className="w-full flex justify-center"
                          style={{ height: "150px" }}
                        >
                          <div
                            className="w-full max-w-[44px] rounded-t bg-gradient-to-t from-copper-600 to-gold-400 self-end transition-all duration-500"
                            style={{ height: `${Math.max(pct, 2)}%` }}
                            title={`${fmtShares(f.cumulative_shares)} cumulative shares as of ${fmtDate(f.announced_date)}`}
                          />
                        </div>
                        <span className="text-[10px] text-slate-500">
                          {new Date(f.announced_date).toLocaleDateString(
                            "en-US",
                            { month: "short", year: "2-digit" },
                          )}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Financings table */}
              <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-sm font-semibold text-gold-400">
                    Financing History
                  </h2>
                  <ExportButton
                    filename={`dilution-${selected?.ticker || "company"}`}
                    rows={data.financings}
                    columns={[
                      { label: "Announced", value: (f) => f.announced_date },
                      { label: "Type", value: (f) => f.financing_type },
                      { label: "Status", value: (f) => f.status },
                      {
                        label: "Amount raised",
                        value: (f) => f.amount_raised_usd,
                      },
                      {
                        label: "Price per share",
                        value: (f) => f.price_per_share,
                      },
                      { label: "Shares issued", value: (f) => f.shares_issued },
                      {
                        label: "Cumulative shares",
                        value: (f) => f.cumulative_shares,
                      },
                      {
                        label: "Has warrants",
                        value: (f) => (f.has_warrants ? "yes" : "no"),
                      },
                      {
                        label: "Warrant strike",
                        value: (f) => f.warrant_strike_price,
                      },
                      {
                        label: "Warrant expiry",
                        value: (f) => f.warrant_expiry_date,
                      },
                    ]}
                  />
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                        <th className="text-left pb-2 pr-4">Date</th>
                        <th className="text-left pb-2 pr-4">Type</th>
                        <th className="text-right pb-2 pr-4">Amount</th>
                        <th className="text-right pb-2 pr-4">Shares Issued</th>
                        <th className="text-right pb-2 pr-4">Price/sh</th>
                        <th className="text-right pb-2 pr-4">Cumulative</th>
                        <th className="text-left pb-2">Warrants</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.financings.map((f) => (
                        <tr
                          key={f.id}
                          className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="py-2 pr-4 text-slate-400 whitespace-nowrap">
                            {fmtDate(f.announced_date)}
                          </td>
                          <td className="py-2 pr-4 text-slate-300">
                            {fmtType(f.financing_type)}
                          </td>
                          <td className="py-2 pr-4 text-right text-gold-400 font-medium">
                            {fmtMoney(f.amount_raised_usd)}
                          </td>
                          <td className="py-2 pr-4 text-right text-slate-300">
                            {fmtShares(f.shares_issued)}
                          </td>
                          <td className="py-2 pr-4 text-right text-slate-400">
                            {f.price_per_share != null
                              ? `$${f.price_per_share.toFixed(3)}`
                              : "—"}
                          </td>
                          <td className="py-2 pr-4 text-right text-slate-300">
                            {fmtShares(f.cumulative_shares)}
                          </td>
                          <td className="py-2">
                            {f.has_warrants ? (
                              <Badge
                                variant={f.warrant_active ? "warning" : "slate"}
                              >
                                {f.warrant_active ? "Active" : "Expired"}
                                {f.warrant_strike_price != null &&
                                  ` @ $${f.warrant_strike_price.toFixed(2)}`}
                              </Badge>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  &quot;Issued vs Float&quot; is total shares issued through
                  recorded financings as a % of current shares outstanding — an
                  approximate dilution gauge, not an exact float reconstruction.
                  Warrant share counts are not recorded, so overhang is shown as
                  a count of tranches still within their expiry date.
                </p>
              </div>
            </>
          )}

          {!loading && !data && !error && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Search and select a company above to see its dilution history.
            </div>
          )}
        </div>
      </section>
    </>
  );
}
