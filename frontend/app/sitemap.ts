import { MetadataRoute } from "next";
import { companyHref } from "@/lib/companyUrl";

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
      url: `${baseUrl}/investor-tools`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/investor-tools/grade-ranker`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/peer-comparison`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/financing-flow`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/sector-pulse`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/ni43-101-analyzer`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/drill-scanner`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/catalyst-calendar`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/property-valuation`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/investor-tools/portfolio-xray`,
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
  const companyRoutes: MetadataRoute.Sitemap = companies
    .filter(
      (company) =>
        company.name && (company.description || company.brief_description),
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

  return [...staticRoutes, ...companyRoutes, ...propertyRoutes];
}
