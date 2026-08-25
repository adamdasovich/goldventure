import { MetadataRoute } from "next";
import { companyHref } from "@/lib/companyUrl";
import { indexableFacets } from "@/lib/commodityFacets";
import { indexableGlossaryCategories } from "@/lib/glossaryCategories";
import { termPageAnchors } from "@/lib/glossaryTermExtras";
import { lastModifiedFor, safeLastModified } from "@/lib/routeLastModified";
import { TOOLS } from "./investor-tools/tools";

const RESOLVED_API_BASE_URL =
  process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL;

if (process.env.NODE_ENV === "production" && !RESOLVED_API_BASE_URL) {
  // Fail loudly in prod rather than silently emit a static-only sitemap
  // (which would happen if the localhost fallback rejected the connection).
  throw new Error(
    "API_BASE_URL (or NEXT_PUBLIC_API_URL) must be set in production for sitemap generation",
  );
}

const API_BASE_URL = RESOLVED_API_BASE_URL || "http://localhost:8000/api";

// Cache the rendered sitemap for 1 hour — a busy Googlebot crawl shouldn't
// fan out into 20+ API calls per fetch.
//
// The fetches below deliberately use a SHORT revalidate (60s) rather than the
// same 3600. Next persists fetch results in .next/cache/fetch-cache and reuses
// them ACROSS BUILDS, so with a matching hour-long TTL a rebuild made right
// after a data change re-emitted the previous sitemap. On 2026-08-24 four
// companies gained descriptions, two consecutive rebuilds still produced the
// old 378 URLs, and only deleting the fetch cache by hand picked them up. The
// two TTLs also compounded: a route regenerating at the 60-minute mark could
// read fetch data already 60 minutes old, leaving the sitemap up to two hours
// behind reality.
//
// 60s is short enough that any build or hourly regeneration reads current data,
// while still collapsing the ~6 paginated calls made within a single render.
//
// Do NOT use `cache: "no-store"` here. It opts the route into dynamic
// rendering, which conflicts with `export const revalidate` — Next throws
// "Dynamic server usage", every fetch fails, and the sitemap silently
// collapses to 47 URLs with zero companies. Tried on 2026-08-24.
//
// Do NOT "fix" a stale sitemap by adding `rm -rf .next/cache` to the deploy —
// that discards the whole incremental build cache and slows every deploy.
export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = "https://juniorminingintelligence.com";

  // Fetch ALL companies using pagination (page_size=100 to cut request count)
  let companies: any[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/companies/?page=${page}&page_size=100`,
        { next: { revalidate: 60 } },
      );
      if (response.ok) {
        const data = await response.json();
        const results = data.results || [];
        companies = [...companies, ...results];
        hasMore = !!data.next;
        page++;
      } else {
        hasMore = false;
      }
    } catch (error) {
      console.error(
        `Failed to fetch companies page ${page} for sitemap:`,
        error,
      );
      hasMore = false;
    }
  }
  console.log(
    `Sitemap: Fetched ${companies.length} companies from ${page - 1} pages`,
  );

  // Fetch ALL property listings using pagination
  let properties: any[] = [];
  let propPage = 1;
  let hasMoreProps = true;

  while (hasMoreProps) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/properties/listings/?status=active&page=${propPage}&page_size=100`,
        { next: { revalidate: 60 } },
      );
      if (response.ok) {
        const data = await response.json();
        // Handle both array and paginated responses
        if (Array.isArray(data)) {
          properties = data;
          hasMoreProps = false;
        } else {
          const results = data.results || [];
          properties = [...properties, ...results];
          hasMoreProps = !!data.next;
          propPage++;
        }
      } else {
        hasMoreProps = false;
      }
    } catch (error) {
      console.error(
        `Failed to fetch properties page ${propPage} for sitemap:`,
        error,
      );
      hasMoreProps = false;
    }
  }
  console.log(`Sitemap: Fetched ${properties.length} properties`);

  // Static routes
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: lastModifiedFor("/"),
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${baseUrl}/companies`,
      lastModified: lastModifiedFor("/companies"),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/glossary`,
      lastModified: lastModifiedFor("/glossary"),
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/metals`,
      lastModified: lastModifiedFor("/metals"),
      changeFrequency: "hourly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/financial-hub`,
      lastModified: lastModifiedFor("/financial-hub"),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/pricing`,
      lastModified: lastModifiedFor("/pricing"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/properties`,
      lastModified: lastModifiedFor("/properties"),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/store`,
      lastModified: lastModifiedFor("/store"),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/store/vault`,
      lastModified: lastModifiedFor("/store/vault"),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/store/field-gear`,
      lastModified: lastModifiedFor("/store/field-gear"),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/store/resource-library`,
      lastModified: lastModifiedFor("/store/resource-library"),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/closed-financings`,
      lastModified: lastModifiedFor("/closed-financings"),
      changeFrequency: "daily",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides`,
      lastModified: lastModifiedFor("/guides"),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/junior-gold-mining-companies-guide`,
      lastModified: lastModifiedFor(
        "/guides/junior-gold-mining-companies-guide",
      ),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/critical-minerals-guide`,
      lastModified: lastModifiedFor("/guides/critical-minerals-guide"),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-to-read-ni-43-101-report`,
      lastModified: lastModifiedFor("/guides/how-to-read-ni-43-101-report"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/inferred-vs-indicated-vs-measured-resources`,
      lastModified: lastModifiedFor(
        "/guides/inferred-vs-indicated-vs-measured-resources",
      ),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-to-interpret-mining-drill-results`,
      lastModified: lastModifiedFor(
        "/guides/how-to-interpret-mining-drill-results",
      ),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/gold-grade-explained`,
      lastModified: lastModifiedFor("/guides/gold-grade-explained"),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-junior-mining-companies-raise-money`,
      lastModified: lastModifiedFor(
        "/guides/how-junior-mining-companies-raise-money",
      ),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/private-placements-and-warrants`,
      lastModified: lastModifiedFor("/guides/private-placements-and-warrants"),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools`,
      lastModified: lastModifiedFor("/investor-tools"),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    // Derived from the tool catalogue rather than listed by hand — the
    // hand-maintained version silently omitted liquidity-screener and
    // signal-to-noise, so two live tools were never submitted.
    ...TOOLS.filter((t) => t.available).map((t) => ({
      url: `${baseUrl}${t.href}`,
      lastModified: lastModifiedFor(t.href),
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
    {
      url: `${baseUrl}/open-financings`,
      lastModified: lastModifiedFor("/open-financings"),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/reports/weekly`,
      lastModified: lastModifiedFor("/reports/weekly"),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/about`,
      lastModified: lastModifiedFor("/about"),
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/financial-hub/private-placements-guide`,
      lastModified: lastModifiedFor("/financial-hub/private-placements-guide"),
      changeFrequency: "monthly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/financial-hub/subscription-agreements-guide`,
      lastModified: lastModifiedFor(
        "/financial-hub/subscription-agreements-guide",
      ),
      changeFrequency: "monthly",
      priority: 0.6,
    },
  ];

  // Dynamic company routes — exclude thin-content companies to avoid soft 404s
  // and "crawled - currently not indexed". Bar: a real name, some prose, AND at
  // least one project. Description-only shells with no projects read as thin /
  // near-duplicate to Google and dilute crawl budget on a young domain.
  const companyRoutes: MetadataRoute.Sitemap = companies
    .filter(
      (company) =>
        company.name &&
        (company.description || company.brief_description) &&
        (company.project_count ?? 0) > 0,
    )
    .map((company) => ({
      url: `${baseUrl}${companyHref(company)}`,
      // The company page's content changes when the company publishes news, so
      // that date is the honest lastmod. NOT `updated_at`: the daily scrape
      // rewrites every company row whether or not anything changed — 89% of
      // companies carried an updated_at within two days on 2026-08-18 — which
      // told Google all 379 profiles change daily and is why lastmod was being
      // ignored. Companies with no news emit no lastmod rather than a made-up
      // one; an absent date is honest, a fabricated one poisons the rest.
      ...(safeLastModified(company.latest_news_date)
        ? { lastModified: safeLastModified(company.latest_news_date) }
        : {}),
      changeFrequency: "weekly" as const,
      priority: 0.8,
    }));

  // Dynamic property routes
  // Property `updated_at` IS a meaningful signal — listings are edited by their
  // owners, not rewritten nightly by a scraper the way company rows are.
  // Listings without one emit no lastmod rather than today's date.
  const propertyRoutes: MetadataRoute.Sitemap = properties.map((property) => ({
    url: `${baseUrl}/properties/${property.slug}`,
    ...(safeLastModified(property.updated_at)
      ? { lastModified: safeLastModified(property.updated_at) }
      : {}),
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  // Faceted commodity landing pages — mid-tail keyword targets
  // ("gold mining companies", "lithium exploration stocks", etc.).
  //
  // Derived from the same config the pages render from, and filtered by the
  // same MIN_INDEXABLE bar they apply. A hardcoded list here drifted out of
  // sync and submitted facets that were noindexing themselves for having no
  // companies — submitted-plus-noindexed is a quality signal against the domain.
  const commodityFacetRoutes: MetadataRoute.Sitemap = (
    await indexableFacets()
  ).map((facet) => ({
    url: `${baseUrl}/companies/commodity/${facet.slug}`,
    // No lastmod: a facet page's content changes whenever any listed company
    // changes, which we cannot date honestly. Omitting is correct — Google
    // falls back to its own heuristics rather than being told something false.
    changeFrequency: "weekly" as const,
    priority: 0.8,
  }));

  // Glossary category pages — definitional long-tail ("mining geology terms",
  // "junior mining finance terms").
  //
  // Grouped rather than one page per term: definitions average 40 words, so
  // 112 term pages would each be thin, while six category pages carry
  // 377-1,380 words of definitions apiece. Filtered by the same
  // MIN_INDEXABLE_TERMS bar the pages apply, for the reason noted above the
  // commodity facets.
  const glossaryCategoryRoutes: MetadataRoute.Sitemap = (
    await indexableGlossaryCategories()
  ).map((category) => ({
    url: `${baseUrl}/glossary/category/${category.slug}`,
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  // Individual glossary term pages.
  //
  // Only terms with expanded context appear here. A page built on the stored
  // definition alone would be about 40 words, so a term without an entry in
  // TERM_EXTRAS stays on its category page and is never submitted -- the list
  // is derived from the same source the route generates from, so the two
  // cannot drift.
  const glossaryTermRoutes: MetadataRoute.Sitemap = termPageAnchors().map(
    (anchor) => ({
      url: `${baseUrl}/glossary/${anchor}`,
      changeFrequency: "monthly" as const,
      priority: 0.5,
    }),
  );

  // Weekly financing roundup pages (native SEO archive)
  let financingWeeks: any[] = [];
  try {
    const res = await fetch(`${API_BASE_URL}/reports/financings/`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      const data = await res.json();
      financingWeeks = data.weeks || [];
    }
  } catch (error) {
    console.error("Failed to fetch financing roundups for sitemap:", error);
  }
  const financingRoundupRoutes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}/reports/financings`,
      lastModified: lastModifiedFor("/reports/financings"),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    ...financingWeeks.map((w: any) => ({
      url: `${baseUrl}/reports/financings/${w.week_ending}`,
      lastModified:
        safeLastModified(w.generated_at) ??
        safeLastModified(`${w.week_ending}T12:00:00Z`),
      changeFrequency: "monthly" as const,
      priority: 0.6,
    })),
  ];

  return [
    ...staticRoutes,
    ...commodityFacetRoutes,
    ...glossaryCategoryRoutes,
    ...glossaryTermRoutes,
    ...financingRoundupRoutes,
    ...companyRoutes,
    ...propertyRoutes,
  ];
}
