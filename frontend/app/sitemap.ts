import { MetadataRoute } from "next";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = "https://juniorminingintelligence.com";

  // Fetch ALL companies using pagination (API returns 25 per page)
  let companies: any[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    try {
      const response = await fetch(`${API_BASE_URL}/companies/?page=${page}`, {
        cache: "no-store",
      });
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
        `${API_BASE_URL}/properties/listings/?status=active&page=${propPage}`,
        {
          cache: "no-store",
        },
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
      url: `${baseUrl}/companies/${company.id}`,
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
