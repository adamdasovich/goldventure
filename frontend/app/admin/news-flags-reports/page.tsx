"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";

interface ProcessingJobSummary {
  id: number;
  status: string;
  document_type: string;
  progress_message: string;
  error_message: string;
  chunks_created: number;
  created_at: string;
  completed_at: string | null;
}

interface NewsReportFlag {
  id: number;
  company_id: number;
  company_name: string;
  company_website: string;
  news_release_id: number;
  news_title: string;
  news_url: string;
  news_date: string;
  detected_keywords: string[];
  status: string;
  flagged_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string;
  report_url: string;
  report_type: string;
  processing_job: ProcessingJobSummary | null;
}

const REPORT_TYPES: { value: string; label: string }[] = [
  { value: "ni43101", label: "NI 43-101 Technical Report" },
  { value: "pea", label: "Preliminary Economic Assessment (PEA)" },
  { value: "pfs", label: "Prefeasibility Study (PFS)" },
  { value: "dfs", label: "Definitive Feasibility Study (DFS)" },
  { value: "mre", label: "Mineral Resource Estimate (MRE)" },
  { value: "other", label: "Other Technical Report" },
];

const STATUS_TABS: { value: string; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "reviewed_processed", label: "Submitted for Processing" },
  { value: "reviewed_false_positive", label: "Dismissed" },
];

function jobBadgeColor(status: string | undefined): string {
  switch (status) {
    case "pending":
      return "bg-amber-500/20 text-amber-300";
    case "processing":
      return "bg-blue-500/20 text-blue-300";
    case "completed":
      return "bg-emerald-500/20 text-emerald-300";
    case "failed":
      return "bg-red-500/20 text-red-300";
    default:
      return "bg-slate-600/30 text-slate-300";
  }
}

export default function NewsFlagsReportsPage() {
  const { user } = useAuth();
  const [flags, setFlags] = useState<NewsReportFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [selectedFlag, setSelectedFlag] = useState<NewsReportFlag | null>(null);
  const [showProcessModal, setShowProcessModal] = useState(false);
  const [showDismissModal, setShowDismissModal] = useState(false);
  const [reportUrl, setReportUrl] = useState("");
  const [reportType, setReportType] = useState<string>("ni43101");
  const [processNotes, setProcessNotes] = useState("");
  const [dismissNotes, setDismissNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchFlags();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const apiBase = process.env.NEXT_PUBLIC_API_URL;
  const authHeader = () => ({
    Authorization: `Bearer ${
      typeof window !== "undefined" ? localStorage.getItem("accessToken") : ""
    }`,
  });

  const fetchFlags = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(
        `${apiBase}/news-flags-reports/?status=${statusFilter}`,
        { headers: authHeader() },
      );
      if (!res.ok) throw new Error("Failed to fetch report flags");
      setFlags(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const openProcessModal = (flag: NewsReportFlag) => {
    setSelectedFlag(flag);
    setReportUrl("");
    setReportType("ni43101");
    setProcessNotes("");
    setShowProcessModal(true);
  };

  const openDismissModal = (flag: NewsReportFlag) => {
    setSelectedFlag(flag);
    setDismissNotes("");
    setShowDismissModal(true);
  };

  const handleProcess = async () => {
    if (!selectedFlag) return;
    if (!reportUrl.trim()) {
      alert("Report URL is required.");
      return;
    }
    try {
      setSubmitting(true);
      const res = await fetch(
        `${apiBase}/news-flags-reports/${selectedFlag.id}/process-report/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeader() },
          body: JSON.stringify({
            report_url: reportUrl.trim(),
            report_type: reportType,
            notes: processNotes,
          }),
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Failed to submit report");
      }
      const data = await res.json();
      alert(
        `Report queued (job #${data.processing_job_id}). The GPU orchestrator will pick it up within a minute.`,
      );
      setShowProcessModal(false);
      setSelectedFlag(null);
      fetchFlags();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDismiss = async () => {
    if (!selectedFlag) return;
    try {
      setSubmitting(true);
      const res = await fetch(
        `${apiBase}/news-flags-reports/${selectedFlag.id}/dismiss/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeader() },
          body: JSON.stringify({ notes: dismissNotes }),
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Failed to dismiss flag");
      }
      setShowDismissModal(false);
      setSelectedFlag(null);
      fetchFlags();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (!user?.is_superuser) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-slate-100 mb-4">
          Access Denied
        </h1>
        <p className="text-slate-400">Only superusers can access this page.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100 mb-2">
          News Release Technical-Report Flags
        </h1>
        <p className="text-slate-400">
          News releases that mention NI 43-101 / PEA / PFS / DFS / MRE / other
          technical reports. Open the company website, retrieve the report PDF,
          then submit its URL to queue docling processing on the GPU pipeline.
        </p>
      </div>

      <div className="mb-6 flex gap-2 flex-wrap">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === tab.value
                ? "bg-gold-500 text-slate-900"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {!loading && !error && flags.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-400">No flags in this state.</p>
        </div>
      )}

      {!loading && !error && flags.length > 0 && (
        <div className="space-y-4">
          {flags.map((flag) => (
            <div
              key={flag.id}
              className="bg-slate-800/50 border border-slate-700 rounded-lg p-6"
            >
              <div className="flex items-start justify-between mb-4 gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-slate-100 mb-1">
                    {flag.company_name}
                  </h3>
                  <p className="text-slate-300 mb-2">{flag.news_title}</p>
                  <div className="flex items-center gap-4 text-sm text-slate-400 flex-wrap">
                    <span>
                      Release date:{" "}
                      {flag.news_date
                        ? new Date(flag.news_date).toLocaleDateString()
                        : "—"}
                    </span>
                    <span>
                      Flagged: {new Date(flag.flagged_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                {flag.status === "pending" && (
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => openProcessModal(flag)}
                    >
                      Process Report
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openDismissModal(flag)}
                    >
                      Dismiss
                    </Button>
                  </div>
                )}
              </div>

              <div className="mb-3">
                <p className="text-sm text-slate-500 mb-2">
                  Detected keywords:
                </p>
                <div className="flex flex-wrap gap-2">
                  {flag.detected_keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-gold-500/20 text-gold-400 text-xs rounded"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-4 text-sm">
                <a
                  href={flag.news_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold-400 hover:text-gold-300"
                >
                  View news release →
                </a>
                {flag.company_website && (
                  <a
                    href={flag.company_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gold-400 hover:text-gold-300"
                  >
                    Company website →
                  </a>
                )}
              </div>

              {flag.processing_job && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <p className="text-sm text-slate-400 mb-2">
                    Docling job #{flag.processing_job.id}{" "}
                    <span
                      className={`ml-2 inline-block px-2 py-0.5 rounded text-xs ${jobBadgeColor(
                        flag.processing_job.status,
                      )}`}
                    >
                      {flag.processing_job.status}
                    </span>
                  </p>
                  {flag.processing_job.progress_message && (
                    <p className="text-xs text-slate-500">
                      {flag.processing_job.progress_message}
                    </p>
                  )}
                  {flag.processing_job.error_message && (
                    <p className="text-xs text-red-400 mt-1">
                      {flag.processing_job.error_message}
                    </p>
                  )}
                  {flag.processing_job.status === "completed" && (
                    <p className="text-xs text-slate-500 mt-1">
                      Chunks inserted: {flag.processing_job.chunks_created}
                    </p>
                  )}
                  {flag.report_url && (
                    <a
                      href={flag.report_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-gold-400 hover:text-gold-300 break-all"
                    >
                      Report URL: {flag.report_url}
                    </a>
                  )}
                </div>
              )}

              {flag.status !== "pending" && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <p className="text-sm text-slate-400">
                    Reviewed by {flag.reviewed_by} on{" "}
                    {flag.reviewed_at &&
                      new Date(flag.reviewed_at).toLocaleDateString()}
                  </p>
                  {flag.review_notes && (
                    <p className="text-sm text-slate-500 mt-1">
                      {flag.review_notes}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Process Report Modal */}
      {showProcessModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-lg w-full max-h-[calc(100dvh-2rem)] overflow-y-auto overscroll-contain">
            <h2 className="text-xl font-bold text-slate-100 mb-2">
              Submit Report for Processing
            </h2>
            <p className="text-slate-400 text-sm mb-4">
              Paste the direct URL of the report PDF (typically found on the
              company website or on SEDAR+). A DocumentProcessingJob will be
              created; the GPU orchestrator picks it up within a minute, runs
              docling, and inserts chunks into the vector database.
            </p>

            <div className="mb-3 p-3 bg-slate-900 rounded-lg">
              <p className="text-sm text-slate-300">
                <span className="text-slate-500">Company:</span>{" "}
                {selectedFlag.company_name}
              </p>
              <p className="text-sm text-slate-300 mt-1">
                <span className="text-slate-500">News:</span>{" "}
                {selectedFlag.news_title}
              </p>
            </div>

            <label className="block text-sm font-medium text-slate-300 mb-1">
              Report PDF URL
            </label>
            <input
              type="url"
              value={reportUrl}
              onChange={(e) => setReportUrl(e.target.value)}
              placeholder="https://example.com/report.pdf"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 mb-3"
            />

            <label className="block text-sm font-medium text-slate-300 mb-1">
              Report type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 mb-3"
              aria-label="Report type"
            >
              {REPORT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>

            <label className="block text-sm font-medium text-slate-300 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={processNotes}
              onChange={(e) => setProcessNotes(e.target.value)}
              rows={2}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 mb-4"
              placeholder="Anything to record about this submission"
            />

            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={handleProcess}
                disabled={submitting}
                className="flex-1"
              >
                {submitting ? "Submitting..." : "Submit for Processing"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowProcessModal(false);
                  setSelectedFlag(null);
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Dismiss Modal */}
      {showDismissModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full max-h-[calc(100dvh-2rem)] overflow-y-auto overscroll-contain">
            <h2 className="text-xl font-bold text-slate-100 mb-4">
              Dismiss Flag
            </h2>
            <p className="text-slate-400 mb-4">
              Dismiss this flag as a false positive. The release URL/title will
              be added to the report-dismissal list and won&apos;t be re-flagged
              by the report detector (financing detection is unaffected).
            </p>
            <textarea
              value={dismissNotes}
              onChange={(e) => setDismissNotes(e.target.value)}
              rows={3}
              placeholder="Why is this a false positive?"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 mb-4"
            />
            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={handleDismiss}
                disabled={submitting}
                className="flex-1"
              >
                {submitting ? "Dismissing..." : "Dismiss Flag"}
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowDismissModal(false);
                  setSelectedFlag(null);
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
