/**
 * Live platform counts, read from the API rather than typed into copy.
 *
 * Hardcoded totals drift and then lie. "500+ companies" sat on the homepage,
 * /companies, About, four guides and a live Google ad while the database held
 * 396. Replacing it with a hardcoded "396" only reset the clock — it would be
 * wrong on company 397 — which is why prose uses floors ("390+") and rendered
 * figures come from here.
 *
 * Server-side only. Falls back to conservative floors so a failed fetch
 * understates rather than invents.
 */

export interface PlatformStats {
  companies: number;
  projects: number;
  financings: number;
  open_financings: number;
  news_releases: number;
  news_articles: number;
}

/** True floors, not zeros: a failed fetch should read as modest, not broken. */
export const PLATFORM_STATS_FALLBACK: PlatformStats = {
  companies: 390,
  projects: 1300,
  financings: 300,
  open_financings: 20,
  news_releases: 17000,
  news_articles: 1900,
};

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export async function fetchPlatformStats(): Promise<PlatformStats> {
  try {
    const res = await fetch(`${API_BASE_URL}/platform-stats/`, {
      next: { revalidate: 600 },
    });
    if (!res.ok) return PLATFORM_STATS_FALLBACK;
    const data = (await res.json()) as Partial<PlatformStats>;
    if (typeof data.companies !== "number") return PLATFORM_STATS_FALLBACK;
    return { ...PLATFORM_STATS_FALLBACK, ...data } as PlatformStats;
  } catch {
    return PLATFORM_STATS_FALLBACK;
  }
}
