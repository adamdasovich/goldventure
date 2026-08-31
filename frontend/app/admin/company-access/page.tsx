"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { accessRequestAPI } from "@/lib/api";
import type { CompanyAccessRequest } from "@/types/api";
import { Button } from "@/components/ui/Button";

/**
 * Approving company representatives.
 *
 * This is the identity half of the company plan: approving a request sets
 * `user.company`, which is what makes someone a representative at all. Payment
 * is the other half and happens afterwards, on their own company page — so
 * approving costs nothing and grants no editing on its own.
 *
 * The endpoints have existed since the portal was built and had no interface
 * at all; the only way to approve anyone was to call the API by hand, and so
 * nobody ever was. That is why zero of 396 companies have a representative.
 *
 * The admin layout already gates on staff, and the review endpoint re-checks.
 */

const ROLE_LABELS: Record<string, string> = {
  ir_manager: "IR Manager",
  ceo: "CEO",
  cfo: "CFO",
  marketing: "Marketing",
  communications: "Communications",
  other: "Other",
};

function formatWhen(iso: string | null | undefined) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Does the work email look like it belongs to the company's own domain?
 *  A hint, not a verdict — plenty of legitimate IR people use an agency
 *  address, so this colours the row rather than deciding anything. */
function emailMatchesCompany(email: string, companyName: string) {
  const domain = (email.split("@")[1] || "").toLowerCase();
  if (!domain) return false;
  const stem = domain.split(".")[0];
  if (stem.length < 4) return false;
  const name = companyName.toLowerCase().replace(/[^a-z]/g, "");
  return name.includes(stem) || stem.includes(name.slice(0, 8));
}

export default function CompanyAccessAdminPage() {
  const { accessToken } = useAuth();
  const [requests, setRequests] = useState<CompanyAccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [working, setWorking] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const res = await accessRequestAPI.getPending(accessToken);
      setRequests(res.results || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load pending requests.",
      );
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  const review = async (
    request: CompanyAccessRequest,
    action: "approve" | "reject",
  ) => {
    if (!accessToken) return;
    if (
      action === "approve" &&
      !confirm(
        `Approve ${request.user_name || request.user_email} as a representative of ${request.company_name}?\n\n` +
          `They will be able to subscribe on its behalf and, once paid, edit its page.`,
      )
    ) {
      return;
    }

    setWorking(request.id);
    setError(null);
    try {
      const res = await accessRequestAPI.review(
        accessToken,
        request.id,
        action,
        notes[request.id],
      );
      setMessage(res.message);
      // Drop it from the list rather than refetching the world.
      setRequests((prev) => prev.filter((r) => r.id !== request.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed.");
    } finally {
      setWorking(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Company Access</h2>
          <p className="text-sm text-slate-400">
            Requests from people asking to manage a company&apos;s page.
            Approving verifies who they are; the company still has to subscribe
            before anything can be edited.
          </p>
        </div>
        <Button variant="secondary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </Button>
      </div>

      {message && (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
          {message}
        </p>
      )}
      {error && (
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {loading ? (
        <p className="p-4 text-sm text-slate-500">Loading…</p>
      ) : requests.length === 0 ? (
        <div className="rounded-lg border border-slate-700 bg-slate-800/40 p-8 text-center">
          <p className="text-sm text-slate-400">
            No requests waiting. When someone opens their company&apos;s page
            and asks for access, it appears here.
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {requests.map((r) => {
            const domainMatch = emailMatchesCompany(
              r.work_email || "",
              r.company_name || "",
            );
            return (
              <li
                key={r.id}
                className="rounded-lg border border-slate-700 bg-slate-800/40 p-4"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold text-slate-100">
                    {r.company_name}
                    {r.company_ticker && (
                      <span className="ml-2 text-xs text-slate-500">
                        {r.company_ticker}
                      </span>
                    )}
                  </h3>
                  <span className="text-xs text-slate-500">
                    requested {formatWhen(r.created_at)}
                  </span>
                </div>

                <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Person</dt>
                    <dd className="text-slate-200">
                      {r.user_name || "—"}{" "}
                      <span className="text-slate-500">({r.user_email})</span>
                    </dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500">Role</dt>
                    <dd className="text-slate-200">
                      {ROLE_LABELS[r.role] || r.role}
                      {r.job_title ? ` — ${r.job_title}` : ""}
                    </dd>
                  </div>
                  <div className="flex gap-2 sm:col-span-2">
                    <dt className="text-slate-500">Work email</dt>
                    <dd
                      className={
                        domainMatch ? "text-emerald-300" : "text-amber-300"
                      }
                      title={
                        domainMatch
                          ? "Domain looks like the company's own"
                          : "Domain does not obviously match the company — worth checking"
                      }
                    >
                      {r.work_email}
                    </dd>
                  </div>
                </dl>

                {r.justification && (
                  <p className="mt-3 whitespace-pre-wrap rounded-lg bg-slate-900/60 p-3 text-sm text-slate-300">
                    {r.justification}
                  </p>
                )}

                <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
                  <input
                    type="text"
                    value={notes[r.id] || ""}
                    onChange={(e) =>
                      setNotes({ ...notes, [r.id]: e.target.value })
                    }
                    placeholder="Note (optional) — kept on the request"
                    className="min-h-11 flex-1 rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-gold-500/70"
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      onClick={() => review(r, "approve")}
                      disabled={working === r.id}
                    >
                      {working === r.id ? "Working…" : "Approve"}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => review(r, "reject")}
                      disabled={working === r.id}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
