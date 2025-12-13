import { MetadataRoute } from 'next';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://juniorgoldminingintelligence.com';

  // Fetch all companies for dynamic routes
  let companies: any[] = [];
  try {
    const response = await fetch(`${API_BASE_URL}/companies/`, {
      cache: 'no-store',
    });
    if (response.ok) {
      const data = await response.json();
      companies = data.results || [];
    }
  } catch (error) {
    console.error('Failed to fetch companies for sitemap:', error);
  }

  // Fetch property listings for dynamic routes
  let properties: any[] = [];
  try {
    const response = await fetch(`${API_BASE_URL}/properties/listings/?status=active`, {
      cache: 'no-store',
    });
    if (response.ok) {
      const data = await response.json();
      properties = Array.isArray(data) ? data : data.results || [];
    }
  } catch (error) {
    console.error('Failed to fetch properties for sitemap:', error);
  }

  // Static routes
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${baseUrl}/companies`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
    {
      url: `${baseUrl}/metals`,
      lastModified: new Date(),
      changeFrequency: 'hourly',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/financial-hub`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/properties`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.8,
    },
  ];

  // Dynamic company routes
  const companyRoutes: MetadataRoute.Sitemap = companies.map((company) => ({
    url: `${baseUrl}/companies/${company.id}`,
    lastModified: new Date(company.updated_at || new Date()),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  // Dynamic property routes
  const propertyRoutes: MetadataRoute.Sitemap = properties.map((property) => ({
    url: `${baseUrl}/properties/${property.slug}`,
    lastModified: new Date(property.updated_at || new Date()),
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  return [...staticRoutes, ...companyRoutes, ...propertyRoutes];
}
