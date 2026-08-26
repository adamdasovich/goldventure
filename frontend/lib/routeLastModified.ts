/**
 * Real last-modified dates for static routes, used by the sitemap.
 *
 * WHY THIS FILE EXISTS
 *
 * Every static route previously emitted `lastModified: new Date()`. Because
 * the sitemap regenerates hourly, that meant all 53 static URLs claimed to
 * have changed at the exact moment the sitemap was built — a fresh timestamp
 * every hour, forever.
 *
 * Google only honours `lastmod` when it is "consistently and verifiably
 * accurate". A sitemap where everything was modified seconds ago fails that
 * test, and the documented consequence is that lastmod is ignored for the
 * whole site. On 2026-08-18 Search Console had not re-read this sitemap since
 * 2026-02-10, and this was the most likely contributing signal.
 *
 * The dates below were seeded from git history — the last commit that touched
 * each route's page file — so they started truthful.
 *
 * MAINTENANCE: when you make a *content* change to one of these pages, update
 * its date here. A styling tweak is not a content change and should not be
 * recorded as one; claiming freshness that does not exist is the exact problem
 * this file was created to fix. Routes absent from this map emit no lastmod at
 * all, which is the correct behaviour when the date is unknown — Google falls
 * back to its own heuristics rather than being told something false.
 */
export const ROUTE_LAST_MODIFIED: Record<string, string> = {
  "/": "2026-05-28",
  "/companies": "2026-08-09",
  "/glossary": "2026-08-04",
  "/metals": "2026-08-04",
  "/financial-hub": "2026-01-04",
  "/financial-hub/subscription-agreements-guide": "2025-12-15",
  "/pricing": "2026-08-18",
  "/properties": "2025-12-14",
  "/store": "2025-12-17",
  "/store/vault": "2025-12-17",
  "/store/field-gear": "2025-12-17",
  "/store/resource-library": "2025-12-17",
  "/closed-financings": "2026-08-04",
  "/open-financings": "2026-08-04",
  "/about": "2026-01-05",

  // Guides
  "/guides": "2026-08-10",
  "/guides/junior-gold-mining-companies-guide": "2026-05-28",
  "/guides/critical-minerals-guide": "2026-01-24",
  "/guides/how-to-read-ni-43-101-report": "2026-05-28",
  "/guides/inferred-vs-indicated-vs-measured-resources": "2026-05-28",
  "/guides/how-to-interpret-mining-drill-results": "2026-05-28",
  "/guides/gold-grade-explained": "2026-05-28",
  "/guides/how-junior-mining-companies-raise-money": "2026-08-18",
  "/guides/private-placements-and-warrants": "2026-08-10",

  // Reports
  "/reports/weekly": "2026-05-29",
  "/reports/financings": "2026-08-09",

  // Investor tools — the index and all 19 tool pages were rewritten from
  // stub pages into full content on 2026-08-18/19.
  "/investor-tools": "2026-08-18",
  "/investor-tools/drill-scanner": "2026-08-18",
  "/investor-tools/liquidity-screener": "2026-08-18",
  "/investor-tools/signal-to-noise": "2026-08-18",
  "/investor-tools/warrant-radar": "2026-08-18",
  "/investor-tools/peer-comparison": "2026-08-18",
  "/investor-tools/metal-correlation": "2026-08-18",
  "/investor-tools/dilution-tracker": "2026-08-18",
  "/investor-tools/resource-growth": "2026-08-18",
  "/investor-tools/ni43-101-analyzer": "2026-08-18",
  "/investor-tools/grade-ranker": "2026-08-19",
  "/investor-tools/catalyst-impact": "2026-08-19",
  "/investor-tools/unusual-activity": "2026-08-19",
  "/investor-tools/due-diligence": "2026-08-19",
  "/investor-tools/portfolio-xray": "2026-08-19",
  "/investor-tools/financing-flow": "2026-08-19",
  "/investor-tools/stock-comparator": "2026-08-19",
  "/investor-tools/sector-pulse": "2026-08-19",
  "/investor-tools/catalyst-calendar": "2026-08-19",
  "/investor-tools/property-valuation": "2026-08-19",
};

/**
 * lastModified for a static route, or undefined when we do not know.
 *
 * Returning undefined omits the tag. That is deliberate: an absent lastmod is
 * honest, whereas a fabricated one degrades every other lastmod on the site.
 */
export function lastModifiedFor(path: string): Date | undefined {
  const iso = ROUTE_LAST_MODIFIED[path];
  return iso ? new Date(`${iso}T00:00:00Z`) : undefined;
}

/**
 * Turn a date coming from the API into a lastmod we are willing to publish.
 *
 * Returns undefined for anything missing or unparseable, and clamps future
 * dates to now. Four companies were emitting a lastmod ahead of today —
 * 2026-11-02 in the worst case — because a mis-parsed release_date had put a
 * press release in the future. A lastmod that has not happened yet is invalid
 * and undermines the credibility of every other date in the file, so the
 * sitemap defends against bad upstream data rather than trusting it.
 *
 * The underlying date-parsing bug is a separate matter; this stops it reaching
 * Google either way.
 */
export function safeLastModified(value?: string | null): Date | undefined {
  if (!value) return undefined;
  const d = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  if (Number.isNaN(d.getTime())) return undefined;
  const now = new Date();
  return d > now ? now : d;
}
