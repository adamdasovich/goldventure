/**
 * Helpers for the `/companies/<id>/news-releases/` payload.
 *
 * That endpoint returns two buckets, `financial` and `non_financial`, but the
 * names are misleading: `non_financial` is actually *every* release for the
 * company and `financial` is the `is_material` subset of it. Anything that
 * concatenates the two buckets therefore lists each financing release twice,
 * so every consumer runs the result through `dedupeReleases`.
 */

type ReleaseLike = {
  id?: number | string;
  url?: string;
  title?: string;
  release_date?: string;
};

/**
 * Drop duplicate releases, keeping first-seen order. Matches on `id` when the
 * record has one, otherwise falls back to url, then title+date — the same
 * release can arrive from different buckets without a stable id only if the
 * serializer changes, but the fallback keeps that from resurfacing dupes.
 */
export function dedupeReleases<T extends ReleaseLike>(releases: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];

  for (const release of releases) {
    if (!release) continue;
    const key =
      release.id != null
        ? `id:${release.id}`
        : release.url
          ? `url:${release.url}`
          : `t:${release.title ?? ""}|${release.release_date ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(release);
  }

  return out;
}
