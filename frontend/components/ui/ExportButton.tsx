"use client";

import { useSyncExternalStore } from "react";

import { Button } from "@/components/ui/Button";
import { exportCsv, type CsvColumn } from "@/lib/exportCsv";
import {
  getTierGateServerSnapshot,
  getTierGateSnapshot,
  subscribeTierGate,
} from "@/lib/tierGate";

interface ExportButtonProps<T> {
  filename: string;
  columns: CsvColumn<T>[];
  rows: T[];
  /** Optional label override; defaults to "Export CSV". */
  label?: string;
  className?: string;
}

/**
 * Download-as-CSV control for a tool's result table.
 *
 * Reads the tier gate so a gated caller is told the file is a preview rather
 * than being handed a truncated table that looks complete. Disabled when there
 * is nothing to export, since a header-only file reads as a broken download.
 */
export default function ExportButton<T>({
  filename,
  columns,
  rows,
  label = "Export CSV",
  className,
}: ExportButtonProps<T>) {
  const gate = useSyncExternalStore(
    subscribeTierGate,
    getTierGateSnapshot,
    getTierGateServerSnapshot,
  );

  const empty = rows.length === 0;
  const tierName =
    gate.requiredTier.charAt(0).toUpperCase() + gate.requiredTier.slice(1);

  return (
    <Button
      variant="ghost"
      size="sm"
      className={className}
      disabled={empty}
      onClick={() => exportCsv({ filename, columns, rows })}
      title={
        empty
          ? "Nothing to export yet"
          : gate.isLocked
            ? `Exports the ${rows.length} rows shown. The rest need ${tierName}.`
            : `Export ${rows.length} rows as CSV`
      }
    >
      {gate.isLocked && !empty ? `${label} (preview)` : label}
    </Button>
  );
}
