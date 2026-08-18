/**
 * CSV export for investor-tool tables.
 *
 * Tier-gate awareness matters here. The backend truncates gated responses and
 * `applyTierGate` strips the redacted stubs before a page ever renders them, so
 * by the time rows reach an export button they are already only the rows the
 * caller is entitled to. Writing those to a file called
 * `peer-comparison-2026-08-14.csv` would hand someone a three-row file that
 * looks like the complete answer. So a gated export is named `-preview` and the
 * button says so; the file itself stays clean, because a comment row would
 * break the spreadsheet import this exists to serve.
 */

import { getTierGateSnapshot } from "@/lib/tierGate";

export interface CsvColumn<T> {
  /** Header text. */
  label: string;
  /** Cell value. Return null/undefined for a blank cell. */
  value: (row: T) => string | number | null | undefined;
}

/** Quote a single field per RFC 4180. */
function escapeCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  // Quote when the value contains a delimiter, quote, or any newline.
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function toCsv<T>(columns: CsvColumn<T>[], rows: T[]): string {
  const header = columns.map((c) => escapeCell(c.label)).join(",");
  const body = rows.map((row) =>
    columns.map((c) => escapeCell(c.value(row))).join(","),
  );
  return [header, ...body].join("\r\n");
}

export interface ExportOptions<T> {
  /** Base filename, no extension — a date and any preview marker are appended. */
  filename: string;
  columns: CsvColumn<T>[];
  rows: T[];
}

/**
 * Serialize rows and trigger a download.
 *
 * Returns whether the export was gated, so a caller can surface that if it
 * wants to; the filename already carries the signal either way.
 */
export function exportCsv<T>({
  filename,
  columns,
  rows,
}: ExportOptions<T>): boolean {
  const gated = getTierGateSnapshot().isLocked;
  const stamp = new Date().toISOString().slice(0, 10);
  const name = `${filename}-${stamp}${gated ? "-preview" : ""}.csv`;

  // The BOM keeps Excel from mangling non-ASCII company names on open.
  const blob = new Blob(["﻿" + toCsv(columns, rows)], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  return gated;
}
