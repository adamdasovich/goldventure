import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = "https://juniorminingintelligence.com";

  // /_next/ is intentionally NOT disallowed — Googlebot needs the JS
  // chunks to render the page. /api/ and /admin/ stay blocked.
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/admin/"],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
