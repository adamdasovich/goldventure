"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";

interface SourceFlag {
  flag_id: number;
  news_title: string;
  news_url: string;
  news_date: string | null;
  project_name: string;
  document_category: string;
  hunt_status: string;
  review_notes: string;
  auto_queued: boolean;
}

interface QueueJob {
  id: number;
  url: string;
  document_type: string;
  company_name: string;
  project_name: string;
  status: string;
  progress_message: string;
  error_message: string;
  chunks_created: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_by: string | null;
  source_flag: SourceFlag | null;
  document: { id: number; title: string; document_type: string } | null;
}

const SOURCE_TABS: { value: string; label: string; hint: string }[] = [
  {
    value: "technical",
    label: "Technical reports",
    hint: "NI 43-101, PEA and technical report jobs, however they were queued.",
  },
  {
    value: "flags",
    label: "From report flags",
    hint: "Only jobs still linked to a technical-report flag. A flag reopened after review clears that link, so its job drops out of this view even though the document is still queued.",
  },
  {
    value: "all",
    label: "All documents",
    hint: "The whole processing table, including every news-release PDF and corporate presentation the platform has processed.",
  },
];

const STATUS_TABS: { value: string; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
  { value: "all", label: "All" },
];

function statusBadge(status: string): string {
  switch (status) {
    case "pending":
      return "bg-amber-500/20 text-amber-300";
    case "processing":
      return "bg-blue-500/20 text-blue-300";
    case "completed":
      return "bg-emerald-500/20 text-emerald-300";
    case "failed":
      return "bg-red-500/20 text-red-300";
    case "cancelled":
      return "bg-slate-600/40 text-slate-300";
    default:
      return "bg-slate-600/30 text-slate-300";
  }
}

function fileName(url: string): string {
  try {
    const path = new URL(url).pathname;
    return decodeURIComponent(path.split("/").filter(Boolean).pop() || url);
  } catch {
    return url;
  }
}

export default function DocumentQueuePage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<QueueJob[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [source, setSource] = useState("technical");
  const [cancelTarget, setCancelTarget] = useState<QueueJob | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL;
  const authHeader = () => ({
    Authorization: `Bearer ${
      typeof window !== "undefined" ? localStorage.getItem("accessToken") : ""
    }`,
  });

  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, source]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const [jobsRes, countsRes] = await Promise.all([
        fetch(
          `${apiBase}/document-queue/?status=${statusFilter}&source=${source}`,
          { headers: authHeader() },
        ),
        fetch(`${apiBase}/document-queue/counts/?source=${source}`, {
          headers: authHeader(),
        }),
      ]);
      if (!jobsRes.ok) throw new Error("Failed to load the document queue");
      setJobs(await jobsRes.json());
      if (countsRes.ok) setCounts(await countsRes.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const confirmCancel = async () => {
    if (!cancelTarget) return;
    try {
      setSubmitting(true);
      const res = await fetch(
        `${apiBase}/document-queue/${cancelTarget.id}/cancel/`,
        {
          method: "POST",
          headers: { ...authHeader(), "Content-Type": "application/json" },
          body: JSON.stringify({ reason: cancelReason }),
        },
      );
      // A non-JSON body (a proxy error page, say) would otherwise surface as
      // "Unexpected token <", which tells the reviewer nothing.
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        // 409 means the worker claimed the job between the page loading and
        // this click. Close the dialog and refresh so the reviewer sees the
        // job's real status instead of a stale Pending they cannot cancel.
        setCancelTarget(null);
        setCancelReason("");
        fetchJobs();
        throw new Error(
          data.error || `Failed to cancel the job (${res.status})`,
        );
      }
      const released = data.released_flag_ids?.length
        ? ` Flag #${data.released_flag_ids.join(", #")} returned to review.`
        : "";
      setNotice(`Job #${cancelTarget.id} cancelled.${released}`);
      setCancelTarget(null);
      setCancelReason("");
      fetchJobs();
    } catch (e: any) {
      setError(e.message);
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
          Document Processing Queue
        </h1>
        <p className="text-slate-400">
          Documents waiting for the GPU pipeline. Each one boots a droplet at
          roughly $1.57/hr and a full NI 43-101 takes about half an hour, so a
          wrong document costs money and puts misleading chunks into the mining
          assistant. Cancel anything that does not belong before it is picked up
          &mdash; only pending jobs can be stopped.
        </p>
      </div>

      <div className="mb-4 flex gap-2 flex-wrap">
        {SOURCE_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setSource(tab.value)}
            title={tab.hint}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors border ${
              source === tab.value
                ? "bg-slate-700 text-slate-100 border-slate-500"
                : "bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <p className="text-xs text-slate-500 mb-4 max-w-3xl">
        {SOURCE_TABS.find((t) => t.value === source)?.hint}
      </p>

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
            {/* The counts endpoint keys the sum as "total"; a status that has
                no jobs is simply absent from the payload, so show 0 rather
                than nothing — an empty badge reads as "not loaded". */}
            {(() => {
              const n =
                tab.value === "all"
                  ? counts["total"]
                  : (counts[tab.value] ?? 0);
              return n !== undefined ? (
                <span className="ml-2 opacity-70">{n}</span>
              ) : null;
            })()}
          </button>
        ))}
      </div>

      {notice && (
        <div className="bg-emerald-500/10 border border-emerald-500/50 rounded-lg p-4 mb-6 flex justify-between gap-4">
          <p className="text-emerald-300">{notice}</p>
          <button
            onClick={() => setNotice(null)}
            className="text-emerald-400 hover:text-emerald-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
        </div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-400">No jobs in this state.</p>
        </div>
      )}

      {!loading && !error && jobs.length > 0 && (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="bg-slate-800/50 border border-slate-700 rounded-lg p-6"
            >
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap mb-2">
                    <h3 className="text-lg font-semibold text-slate-100">
                      {job.company_name || "Unknown company"}
                    </h3>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadge(
                        job.status,
                      )}`}
                    >
                      {job.status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                      {job.document_type}
                    </span>
                    {job.source_flag?.auto_queued && (
                      <span className="px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-300">
                        auto-queued
                      </span>
                    )}
                  </div>

                  <p className="text-slate-300 break-words mb-1">
                    {fileName(job.url)}
                  </p>
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gold-400 hover:text-gold-300 break-all"
                  >
                    View document &rarr;
                  </a>
                </div>

                {job.status === "pending" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setCancelTarget(job);
                      setCancelReason("");
                    }}
                  >
                    Cancel
                  </Button>
                )}
              </div>

              {job.source_flag && (
                <div className="bg-slate-900/50 border border-slate-700 rounded p-4 mb-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                    Why this is queued
                  </p>
                  <p className="text-sm text-slate-300 mb-2">
                    {job.source_flag.news_title}
                  </p>
                  <div className="flex flex-wrap gap-3 text-xs text-slate-400 mb-2">
                    {job.source_flag.project_name && (
                      <span>
                        Project:{" "}
                        <span className="text-slate-300">
                          {job.source_flag.project_name}
                        </span>
                      </span>
                    )}
                    {job.source_flag.document_category && (
                      <span>Category: {job.source_flag.document_category}</span>
                    )}
                    {job.source_flag.news_date && (
                      <span>
                        Announced:{" "}
                        {new Date(
                          job.source_flag.news_date,
                        ).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {job.source_flag.review_notes && (
                    <p className="text-xs text-slate-500 break-words">
                      {job.source_flag.review_notes}
                    </p>
                  )}
                  <a
                    href={job.source_flag.news_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-gold-400 hover:text-gold-300"
                  >
                    Open the announcement &rarr;
                  </a>
                </div>
              )}

              <div className="flex flex-wrap gap-4 text-sm text-slate-400">
                <span>Queued: {new Date(job.created_at).toLocaleString()}</span>
                {job.started_at && (
                  <span>
                    Started: {new Date(job.started_at).toLocaleString()}
                  </span>
                )}
                {job.completed_at && (
                  <span>
                    Finished: {new Date(job.completed_at).toLocaleString()}
                  </span>
                )}
                {job.chunks_created > 0 && (
                  <span>{job.chunks_created} chunks</span>
                )}
                {job.created_by && <span>By: {job.created_by}</span>}
              </div>

              {job.progress_message && (
                <p className="text-sm text-blue-300 mt-2">
                  {job.progress_message}
                </p>
              )}
              {job.error_message && (
                <p className="text-sm text-red-400 mt-2 break-words">
                  {job.error_message}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {cancelTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-slate-100 mb-2">
              Cancel this job?
            </h2>
            <p className="text-sm text-slate-400 mb-4 break-words">
              {fileName(cancelTarget.url)}
            </p>
            {cancelTarget.source_flag && (
              <p className="text-sm text-amber-300 mb-4">
                This document was queued from a technical-report flag.
                Cancelling returns that flag to the review queue with its
                candidate list intact, so the correct report can still be
                submitted.
              </p>
            )}
            <label className="block text-sm text-slate-400 mb-2">
              Reason (optional)
            </label>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              rows={3}
              placeholder="e.g. wrong project, this is a presentation not a technical report"
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 mb-4"
            />
            <div className="flex gap-2 justify-end">
              <Button
                variant="secondary"
                onClick={() => setCancelTarget(null)}
                disabled={submitting}
              >
                Keep it
              </Button>
              <Button
                variant="primary"
                onClick={confirmCancel}
                disabled={submitting}
              >
                {submitting ? "Cancelling..." : "Cancel job"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
