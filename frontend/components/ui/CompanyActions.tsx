"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuth } from "@/contexts/AuthContext";
import { watchlistAPI } from "@/lib/api";

/**
 * Watchlist toggle plus jumps to the other company-scoped tools.
 *
 * Two gaps this closes. Watchlists existed but no tool could add to one, so a
 * user who found something interesting had to go elsewhere and search for it
 * again. And every tool was a dead end: having looked at a company's dilution
 * there was no way to reach its warrant book or its catalyst history without
 * navigating to another tool and re-picking the same company.
 */

interface CompanyActionsProps {
  companyId: number;
  companyName: string;
  /** Slug of the tool rendering this, so it isn't offered as a destination. */
  currentSlug: string;
}

// Tools that accept a `company_id` and are worth reaching from another tool.
const COMPANY_TOOLS: { slug: string; label: string }[] = [
  { slug: "dilution-tracker", label: "Dilution" },
  { slug: "warrant-radar", label: "Warrants" },
  { slug: "catalyst-impact", label: "Catalyst impact" },
  { slug: "resource-growth", label: "Resources" },
  { slug: "unusual-activity", label: "Unusual activity" },
  { slug: "due-diligence", label: "Due diligence" },
  { slug: "peer-comparison", label: "Peers" },
];

export default function CompanyActions({
  companyId,
  companyName,
  currentSlug,
}: CompanyActionsProps) {
  const { accessToken } = useAuth();
  const [watched, setWatched] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);

  // Establish current membership so the control doesn't lie on first paint.
  useEffect(() => {
    if (!accessToken) {
      setWatched(null);
      return;
    }
    let cancelled = false;
    watchlistAPI
      .get(accessToken)
      .then((res) => {
        if (cancelled) return;
        const rows = res?.companies ?? res?.results ?? res ?? [];
        const ids = Array.isArray(rows)
          ? rows.map((r: any) => r?.id ?? r?.company_id)
          : [];
        setWatched(ids.includes(companyId));
      })
      .catch(() => {
        if (!cancelled) setWatched(false);
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, companyId]);

  const toggle = async () => {
    if (!accessToken || busy) return;
    setBusy(true);
    // Optimistic: the toggle is cheap to reverse and the round trip is visible.
    const previous = watched;
    setWatched(!watched);
    try {
      const res = await watchlistAPI.toggle(companyId, accessToken);
      setWatched(res.watched);
    } catch {
      setWatched(previous);
    } finally {
      setBusy(false);
    }
  };

  const destinations = COMPANY_TOOLS.filter((t) => t.slug !== currentSlug);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {accessToken && (
        <button
          type="button"
          onClick={toggle}
          disabled={busy || watched === null}
          aria-pressed={watched === true}
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
            watched
              ? "border-gold-500/50 bg-gold-500/15 text-gold-300"
              : "border-slate-700 text-slate-400 hover:border-gold-600 hover:text-gold-400"
          }`}
          title={
            watched
              ? `Remove ${companyName} from your watchlist`
              : `Add ${companyName} to your watchlist`
          }
        >
          <span aria-hidden="true">{watched ? "★" : "☆"}</span>
          {watched ? "On watchlist" : "Watch"}
        </button>
      )}

      <span className="text-xs text-slate-600">Open in:</span>
      {destinations.map((t) => (
        <Link
          key={t.slug}
          href={`/investor-tools/${t.slug}?company_id=${companyId}`}
          className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400 transition-colors hover:border-gold-600 hover:text-gold-400"
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}
