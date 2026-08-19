"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Badge } from "@/components/ui/Badge";
import CompanyActions from "@/components/ui/CompanyActions";
import { Button } from "@/components/ui/Button";
import { toolsAPI } from "@/lib/api";

/* ---------- types ---------- */

interface AvailableCompany {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
}

interface Section {
  rank: number;
  text: string;
  document_id: number | null;
  document_title: string;
  document_date: string | null;
  document_type: string | null;
}

interface SourceDoc {
  document_id: number | null;
  title: string;
}

interface DDData {
  available_companies: AvailableCompany[];
  company?: { id: number; name: string; ticker: string };
  question?: string;
  sections: Section[];
  source_documents?: SourceDoc[];
}

/* ---------- constants ---------- */

const SUGGESTED_QUESTIONS = [
  "What are the metallurgical recovery results?",
  "What is the mineral resource estimate?",
  "What are the key project risks?",
  "What infrastructure is in place at the project?",
  "What permitting is required?",
  "What does the qualified person conclude?",
];

const DOC_TYPE_LABELS: Record<string, string> = {
  ni43101: "NI 43-101",
  presentation: "Presentation",
  financial_stmt: "Financial Statement",
  mda: "MD&A",
  annual_report: "Annual Report",
  factsheet: "Fact Sheet",
  map: "Project Map",
  pea: "PEA",
};

/* ---------- helpers ---------- */

function docTypeLabel(code: string | null): string {
  if (!code) return "Document";
  return (
    DOC_TYPE_LABELS[code] ||
    code.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

/* ---------- page ---------- */

export default function DueDiligenceClient() {
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AvailableCompany | null>(null);
  const [question, setQuestion] = useState("");
  const [data, setData] = useState<DDData | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = (await toolsAPI.dueDiligence({})) as DDData;
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


  const runSearch = useCallback(
    async (q: string) => {
      const query = q.trim();
      if (!selected || !query) return;
      setLoading(true);
      setError(null);
      setSearched(true);
      try {
        const res = (await toolsAPI.dueDiligence({
          company_id: String(selected.id),
          question: query,
        })) as DDData;
        setData(res);
      } catch (e: any) {
        setError(e?.message || "Search failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [selected],
  );

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
                      setSearched(false);
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
                  {!initialLoading && (
                    <p className="text-xs text-slate-500 mt-2">
                      {available.length} companies have processed technical
                      reports available to search.
                    </p>
                  )}
                </div>
              )}
            </div>

            {selected && (
              <div className="border-t border-slate-700/40 pt-3">
                <CompanyActions
                  companyId={selected.id}
                  companyName={selected.name}
                  currentSlug="due-diligence"
                />
              </div>
            )}

            {/* Question */}
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2">
                Due-Diligence Question
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") runSearch(question);
                  }}
                  placeholder="e.g. What are the metallurgical recovery results?"
                  disabled={!selected}
                  className="flex-1 bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-md px-3 py-2 focus:border-gold-500/50 focus:outline-none disabled:opacity-50"
                />
                <Button
                  variant="primary"
                  onClick={() => runSearch(question)}
                  disabled={!selected || !question.trim() || loading}
                >
                  {loading ? "Searching…" : "Search"}
                </Button>
              </div>
              {/* Suggested questions */}
              <div className="flex flex-wrap gap-2 mt-3">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setQuestion(q);
                      runSearch(q);
                    }}
                    disabled={!selected || loading}
                    className="px-3 py-1.5 text-xs rounded-full bg-slate-800/60 border border-slate-700/50 text-slate-300 hover:text-gold-400 hover:border-gold-500/30 transition-all disabled:opacity-40"
                  >
                    {q}
                  </button>
                ))}
              </div>
              {!selected && (
                <p className="text-xs text-slate-500 mt-2">
                  Select a company first.
                </p>
              )}
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto space-y-6">
          {loading && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Searching technical reports…
            </div>
          )}

          {!loading && searched && data && data.sections.length === 0 && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              No relevant passages found in {data.company?.name}&apos;s
              processed reports for that question. Try rephrasing, or the
              company may not have technical reports covering this topic.
            </div>
          )}

          {!loading && data && data.sections.length > 0 && (
            <>
              {/* Sources summary */}
              {data.source_documents && data.source_documents.length > 0 && (
                <div className="glass-card rounded-xl p-5">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                    Drawn from {data.source_documents.length}{" "}
                    {data.source_documents.length === 1
                      ? "document"
                      : "documents"}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {data.source_documents.map((d, i) => (
                      <Badge key={i} variant="slate">
                        {d.title}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Ranked passages */}
              {data.sections.map((s) => (
                <div key={s.rank} className="glass-card rounded-xl p-5 sm:p-6">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center justify-center w-7 h-7 rounded-full bg-gold-500/15 border border-gold-500/30 text-gold-400 text-xs font-bold shrink-0">
                        {s.rank}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-200">
                          {s.document_title}
                        </p>
                        <p className="text-xs text-slate-500">
                          {docTypeLabel(s.document_type)}
                          {s.document_date && ` · ${fmtDate(s.document_date)}`}
                        </p>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {s.text}
                  </p>
                </div>
              ))}

              <p className="text-xs text-slate-500">
                Passages are ranked by relevance via hybrid search (vector +
                keyword) over processed NI 43-101 reports. They are quoted
                verbatim from the source documents — read them in context and
                verify against the full report.
              </p>
            </>
          )}

          {!loading && !searched && (
            <div className="glass-card rounded-xl p-10 text-center text-slate-400">
              Select a company and ask a due-diligence question to see the
              relevant report passages.
            </div>
          )}
        </div>
      </section>
    </>
  );
}
