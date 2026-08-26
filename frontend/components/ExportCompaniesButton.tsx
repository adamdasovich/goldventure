"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";
import UpgradeModal from "@/components/UpgradeModal";

/**
 * CSV download of the company directory. Prospector and above.
 *
 * The button is shown to everyone rather than hidden from free users: a
 * download they can see and cannot use is a far better upgrade prompt than one
 * they never knew existed, and it matches how ToolsGrid renders locked tools.
 *
 * The server enforces the gate independently (requires_tier on
 * export_companies_csv), so this check is presentation only — bypassing it
 * client-side gets a 403, not a file.
 *
 * The fetch carries the auth header manually because the download is a
 * streaming file rather than JSON: we need the Blob to trigger a save, and an
 * anchor href cannot carry an Authorization header.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function ExportCompaniesButton({
  className = "",
}: {
  className?: string;
}) {
  const { subscription, accessToken } = useAuth();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tier = subscription?.effective_tier || "explorer";
  const canExport = tier === "prospector" || tier === "miner";

  const download = async () => {
    if (!canExport) {
      setShowUpgrade(true);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/companies/export/csv/`, {
        headers: accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : undefined,
      });
      if (res.status === 403) {
        // Grant lapsed between page load and click.
        setShowUpgrade(true);
        return;
      }
      if (!res.ok) throw new Error(`Export failed (${res.status})`);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        res.headers
          .get("Content-Disposition")
          ?.match(/filename="([^"]+)"/)?.[1] || "companies.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className={className}>
        <Button
          variant="secondary"
          size="sm"
          onClick={download}
          disabled={busy}
          title={
            canExport
              ? "Download the full company database as CSV"
              : "Included with Prospector"
          }
        >
          {!canExport && (
            <svg
              className="w-4 h-4 mr-2 text-gold-400"
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
          )}
          {busy ? "Preparing…" : "Export CSV"}
        </Button>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </div>

      {showUpgrade && (
        <UpgradeModal
          onClose={() => setShowUpgrade(false)}
          feature="CSV export of the full company database"
          requiredTier="prospector"
        />
      )}
    </>
  );
}
