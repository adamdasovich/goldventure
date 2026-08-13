/**
 * Client-side handling for tier-gated tool responses.
 *
 * The backend (core/entitlements.py) truncates investor-tool payloads for
 * Explorer and anonymous callers: the first few rows come through intact and
 * the remainder are replaced by stubs holding identity fields only, with every
 * other field nulled out.
 *
 * Those stubs must never reach the tool pages' own renderers — a lot of them
 * call .toFixed()/.toLocaleString() straight on numeric columns and would throw
 * on a null. So we strip the stubs out of the payload here and hand them to the
 * upgrade banner instead, which reads identity fields only.
 */

export interface LockedRow {
  [key: string]: unknown;
  is_locked: true;
}

export interface TierGateState {
  isLocked: boolean;
  requiredTier: string;
  lockedCount: number;
  previewCount: number;
  lockedRows: LockedRow[];
}

// Stable reference so useSyncExternalStore doesn't see a new snapshot on every
// read while the gate is inactive.
const UNGATED: TierGateState = {
  isLocked: false,
  requiredTier: "prospector",
  lockedCount: 0,
  previewCount: 0,
  lockedRows: [],
};

let state: TierGateState = UNGATED;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

export function subscribeTierGate(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getTierGateSnapshot(): TierGateState {
  return state;
}

/** SSR snapshot — always ungated, since there's no fetch on the server. */
export function getTierGateServerSnapshot(): TierGateState {
  return UNGATED;
}

export function clearTierGate(): void {
  if (state !== UNGATED) {
    state = UNGATED;
    emit();
  }
}

/**
 * Strip locked stub rows out of a tool response and publish the gate state.
 *
 * Returns the payload with every top-level array filtered down to its unlocked
 * rows. A payload the backend didn't gate passes through untouched and resets
 * the banner, so moving from a gated tool to a free one clears it.
 */
export function applyTierGate<T extends Record<string, unknown>>(
  payload: T,
): T {
  if (!payload || typeof payload !== "object") {
    return payload;
  }

  if (!(payload as { is_locked?: boolean }).is_locked) {
    clearTierGate();
    return payload;
  }

  const gated = payload as T & {
    required_tier?: string;
    locked_count?: number;
    preview_count?: number;
  };

  const lockedRows: LockedRow[] = [];
  const cleaned: Record<string, unknown> = { ...payload };

  for (const [key, value] of Object.entries(payload)) {
    if (!Array.isArray(value)) continue;

    const unlocked: unknown[] = [];
    for (const row of value) {
      if (
        row &&
        typeof row === "object" &&
        (row as LockedRow).is_locked === true
      ) {
        lockedRows.push(row as LockedRow);
      } else {
        unlocked.push(row);
      }
    }
    if (unlocked.length !== value.length) {
      cleaned[key] = unlocked;
    }
  }

  state = {
    isLocked: true,
    requiredTier: gated.required_tier ?? "prospector",
    lockedCount: gated.locked_count ?? lockedRows.length,
    previewCount: gated.preview_count ?? 0,
    lockedRows,
  };
  emit();

  return cleaned as T;
}

/** Best-effort display label for a locked stub. */
export function lockedRowLabel(row: LockedRow): string | null {
  const name =
    (row.company_name as string) ??
    (row.name as string) ??
    (row.title as string) ??
    null;
  const ticker =
    (row.company_ticker as string) ??
    (row.ticker as string) ??
    (row.ticker_symbol as string) ??
    (row.symbol as string) ??
    null;

  if (name && ticker) return `${name} (${ticker})`;
  return name ?? ticker ?? null;
}
