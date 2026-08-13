"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import {
  clearTierGate,
  getTierGateServerSnapshot,
  getTierGateSnapshot,
  lockedRowLabel,
  subscribeTierGate,
} from "@/lib/tierGate";

/**
 * Upgrade prompt for tier-gated investor tools.
 *
 * Mounted once in the investor-tools layout rather than in each tool page: the
 * pages render their results in 17 different shapes, and the API layer already
 * knows when a response came back gated. Styling mirrors the open-financings
 * UpgradeBanner so the two paywalls read as one thing.
 */
export default function TierGateBanner() {
  const gate = useSyncExternalStore(
    subscribeTierGate,
    getTierGateSnapshot,
    getTierGateServerSnapshot,
  );
  const pathname = usePathname();

  // Drop the banner when moving between tools so a stale count never carries
  // over to a page whose own request hasn't resolved yet.
  useEffect(() => {
    clearTierGate();
  }, [pathname]);

  if (!gate.isLocked) return null;

  const tierName =
    gate.requiredTier.charAt(0).toUpperCase() + gate.requiredTier.slice(1);

  // Tools that gate parallel lists (stock-comparator's `series` + `summary`,
  // warrant-radar's `companies` + `tranches`) emit one stub per list, so the
  // same company shows up more than once. Dedupe by label, and prefer that
  // count over locked_count, which sums across keys and double-counts.
  const names = Array.from(
    new Set(
      gate.lockedRows
        .map(lockedRowLabel)
        .filter((label): label is string => Boolean(label)),
    ),
  );
  const displayCount = names.length > 0 ? names.length : gate.lockedCount;
  const shown = names.slice(0, 6);
  const remaining = names.length - shown.length;

  return (
    <div className="my-6">
      <Card
        variant="glass-card"
        className="border-gold-500/40 bg-gradient-to-r from-gold-500/10 via-copper-500/10 to-gold-500/10"
      >
        <CardContent className="p-6 flex flex-col gap-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-gold-500/20 flex items-center justify-center flex-shrink-0">
                <svg
                  className="w-5 h-5 text-gold-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">
                  {displayCount > 0 ? (
                    <>
                      {displayCount} more result
                      {displayCount !== 1 ? "s" : ""} —{" "}
                    </>
                  ) : null}
                  <span className="text-gold-400">unlock with {tierName}</span>
                </h3>
                <p className="text-sm text-slate-400">
                  {gate.previewCount > 0
                    ? `You're seeing the first ${gate.previewCount} of this tool's results. `
                    : ""}
                  Upgrade for the full data set across every investor tool.
                </p>
              </div>
            </div>
            <Link href="/pricing">
              <Button variant="primary" size="lg" className="whitespace-nowrap">
                Upgrade →
              </Button>
            </Link>
          </div>

          {shown.length > 0 && (
            <div className="border-t border-gold-500/20 pt-4">
              <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                Hidden from your results
              </p>
              <div className="flex flex-wrap gap-2">
                {shown.map((label, i) => (
                  <span
                    key={`${label}-${i}`}
                    className="inline-flex items-center gap-1.5 rounded-md bg-slate-800/60 border border-slate-700/60 px-2.5 py-1 text-xs text-slate-400"
                  >
                    <svg
                      className="w-3 h-3 text-slate-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                      />
                    </svg>
                    {label}
                  </span>
                ))}
                {remaining > 0 && (
                  <span className="inline-flex items-center px-2.5 py-1 text-xs text-slate-500">
                    +{remaining} more
                  </span>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
