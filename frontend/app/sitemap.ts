import { MetadataRoute } from "next";
import { companyHref } from "@/lib/companyUrl";
import { indexableFacets } from "@/lib/commodityFacets";
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

// Cache the sitemap itself for 1 hour — a busy Googlebot crawl shouldn't
// fan out into 20+ API calls per fetch.
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
        { next: { revalidate: 3600 } },
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
        { next: { revalidate: 3600 } },
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
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${baseUrl}/companies`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/glossary`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/metals`,
      lastModified: new Date(),
      changeFrequency: "hourly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/financial-hub`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/pricing`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/properties`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/store`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/store/vault`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/store/field-gear`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/store/resource-library`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/closed-financings`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/junior-gold-mining-companies-guide`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/critical-minerals-guide`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-to-read-ni-43-101-report`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/inferred-vs-indicated-vs-measured-resources`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-to-interpret-mining-drill-results`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/gold-grade-explained`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/guides/how-junior-mining-companies-raise-money`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/guides/private-placements-and-warrants`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    // Derived from the tool catalogue rather than listed by hand — the
    // hand-maintained version silently omitted liquidity-screener and
    // signal-to-noise, so two live tools were never submitted.
    ...TOOLS.filter((t) => t.available).map((t) => ({
      url: `${baseUrl}${t.href}`,
      lastModified: new Date(),
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
    {
      url: `${baseUrl}/open-financings`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/reports/weekly`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/about`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/financial-hub/private-placements-guide`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/financial-hub/subscription-agreements-guide`,
      lastModified: new Date(),
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
      lastModified: new Date(company.updated_at || new Date()),
      changeFrequency: "weekly" as const,
      priority: 0.8,
    }));

  // Dynamic property routes
  const propertyRoutes: MetadataRoute.Sitemap = properties.map((property) => ({
    url: `${baseUrl}/properties/${property.slug}`,
    lastModified: new Date(property.updated_at || new Date()),
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
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.8,
  }));

  // Weekly financing roundup pages (native SEO archive)
  let financingWeeks: any[] = [];
  try {
    const res = await fetch(`${API_BASE_URL}/reports/financings/`, {
      next: { revalidate: 3600 },
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
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    ...financingWeeks.map((w: any) => ({
      url: `${baseUrl}/reports/financings/${w.week_ending}`,
      lastModified: new Date(w.generated_at || `${w.week_ending}T12:00:00Z`),
      changeFrequency: "monthly" as const,
      priority: 0.6,
    })),
  ];

  return [
    ...staticRoutes,
    ...commodityFacetRoutes,
    ...financingRoundupRoutes,
    ...companyRoutes,
    ...propertyRoutes,
  ];
}
