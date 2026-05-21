"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { watchlistAPI } from "@/lib/api";

interface WatchButtonProps {
  companyId: number;
  /** Called when an unauthenticated user clicks — parent opens a login modal. */
  onRequireLogin?: () => void;
}

const STAR_PATH =
  "M11.48 3.5a.562.562 0 011.04 0l2.125 5.11a.563.563 0 00.475.346l5.518.442c.5.04.703.663.322.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.611l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.322-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z";

/**
 * "Watch" toggle — adds/removes a company from the user's watchlist, which
 * powers the dashboard Daily Briefing.
 */
export default function WatchButton({
  companyId,
  onRequireLogin,
}: WatchButtonProps) {
  const { accessToken } = useAuth();
  const [watched, setWatched] = useState(false);
  const [loading, setLoading] = useState(false);

  // Resolve the initial watched state from the user's watchlist.
  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await watchlistAPI.get(accessToken);
        if (!cancelled) {
          const ids = (res.companies || []).map((c: any) => c.id);
          setWatched(ids.includes(companyId));
        }
      } catch {
        /* non-critical — leave as not watched */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken, companyId]);

  const handleClick = async () => {
    if (!accessToken) {
      onRequireLogin?.();
      return;
    }
    if (loading) return;
    setLoading(true);
    try {
      const res = await watchlistAPI.toggle(companyId, accessToken);
      setWatched(res.watched);
    } catch {
      /* swallow — the button simply won't change state */
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      aria-pressed={watched ? "true" : "false"}
      title={
        !accessToken
          ? "Log in to watch this company"
          : watched
            ? "Remove from your watchlist"
            : "Add to your watchlist"
      }
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all disabled:opacity-60 ${
        watched
          ? "bg-gold-500/15 border-gold-500/40 text-gold-300 hover:bg-gold-500/25"
          : "bg-slate-800/60 border-slate-700/50 text-slate-300 hover:text-gold-400 hover:border-gold-500/40"
      }`}
    >
      <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill={watched ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth={1.8}
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d={STAR_PATH} />
      </svg>
      {watched ? "Watching" : "Watch"}
    </button>
  );
}
