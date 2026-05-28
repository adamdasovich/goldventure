import type { Metadata } from "next";
import { companyHref, parseCompanyIdParam } from "@/lib/companyUrl";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Props = {
  params: Promise<{ id: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id: rawSegment } = await params;
  const numericId = parseCompanyIdParam(rawSegment);

  if (numericId === null) {
    return {
      title: "Company Not Found",
      alternates: {
        canonical: `https://juniorminingintelligence.com/companies/${rawSegment}`,
      },
    };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/companies/${numericId}/`, {
      next: { revalidate: 3600 },
    });

    if (!response.ok) {
      return {
        title: "Company Not Found",
        alternates: {
          canonical: `https://juniorminingintelligence.com${companyHref({ id: numericId })}`,
        },
      };
    }

    const company = await response.json();
    const canonicalPath = companyHref(company);
    const canonicalUrl = `https://juniorminingintelligence.com${canonicalPath}`;

    // Metal-aware copy — pull commodities from flagship projects if available.
    const commodities: string[] = Array.isArray(company.projects)
      ? Array.from(
          new Set(
            company.projects
              .map((p: any) => (p.primary_commodity || "").toLowerCase())
              .filter(Boolean),
          ),
        )
      : [];
    const primaryCommodity = commodities[0] || "mineral";
    const commodityLabel =
      primaryCommodity.charAt(0).toUpperCase() + primaryCommodity.slice(1);

    // Keep title under ~60 chars: "{name} ({ticker}) | Junior Mining"
    // appended automatically by root layout's title.template.
    const tickerSuffix = company.ticker_symbol
      ? ` (${company.ticker_symbol})`
      : "";
    const title = `${company.name}${tickerSuffix} — ${commodityLabel} Exploration`;
    const description = company.description
      ? `${company.description.substring(0, 155)}...`
      : `${company.name}${company.exchange ? ` (${company.exchange.toUpperCase()}: ${company.ticker_symbol})` : ""} — ${commodityLabel.toLowerCase()} exploration company. Projects, resource estimates, financings, and news.`;

    return {
      title,
      description,
      keywords: [
        company.name,
        company.ticker_symbol,
        `${company.exchange} ${company.ticker_symbol}`,
        `${primaryCommodity} mining stock`,
        "junior mining company",
        "mineral exploration",
        "mining investment",
        company.headquarters || "",
      ].filter(Boolean),
      openGraph: {
        title,
        description,
        type: "website",
        url: canonicalUrl,
        siteName: "Junior Mining Intelligence",
        images: [
          {
            url: `/og/company/${rawSegment}`,
            width: 1200,
            height: 630,
            alt: `${company.name} Company Profile`,
          },
        ],
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        images: [`/og/company/${rawSegment}`],
      },
      alternates: {
        canonical: canonicalUrl,
      },
    };
  } catch (error) {
    console.error("Error generating metadata:", error);
    return {
      title: "Company Profile",
      alternates: {
        canonical: `https://juniorminingintelligence.com${companyHref({ id: numericId })}`,
      },
    };
  }
}

// Emit BreadcrumbList + NewsArticle JSON-LD from the layout (not the page) —
// in Next.js 16, sibling <script> nodes inside a page's Fragment-return alongside
// a Client Component get streamed into RSC chunks instead of being emitted as
// DOM elements. Layout-level <script> tags render reliably.
export default async function CompanyLayout({ children, params }: Props) {
  const { id: rawSegment } = await params;
  const numericId = parseCompanyIdParam(rawSegment);
  if (numericId === null) return <>{children}</>;

  let company: any = null;
  let newsReleases: any[] = [];
  try {
    const [cRes, nRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/news-releases/`, {
        next: { revalidate: 1800 },
      }),
    ]);
    if (cRes.ok) company = await cRes.json();
    if (nRes.ok) {
      const np = await nRes.json().catch(() => null);
      newsReleases = Array.isArray(np)
        ? np
        : [
            ...(np?.financial || []),
            ...(np?.non_financial || []),
            ...(np?.results || []),
            ...(np?.news_releases || []),
          ];
      newsReleases.sort(
        (a, b) =>
          new Date(b.release_date || 0).getTime() -
          new Date(a.release_date || 0).getTime(),
      );
    }
  } catch {
    return <>{children}</>;
  }

  if (!company) return <>{children}</>;

  const canonicalUrl = `https://juniorminingintelligence.com${companyHref(company)}`;

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "Home",
        item: "https://juniorminingintelligence.com",
      },
      {
        "@type": "ListItem",
        position: 2,
        name: "Companies",
        item: "https://juniorminingintelligence.com/companies",
      },
      {
        "@type": "ListItem",
        position: 3,
        name: company.name,
        item: canonicalUrl,
      },
    ],
  };

  const newsArticleJsonLd = newsReleases.slice(0, 10).map((nr: any) => ({
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    headline: nr.title,
    datePublished: nr.release_date,
    dateModified: nr.updated_at || nr.release_date,
    url: nr.url || canonicalUrl,
    publisher: {
      "@type": "Organization",
      name: company.name,
      ...(company.website && { url: company.website }),
    },
    author: { "@type": "Organization", name: company.name },
    ...(nr.summary && { description: nr.summary.slice(0, 280) }),
    mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
  }));

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      {newsArticleJsonLd.map((article, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(article) }}
        />
      ))}
      {children}
    </>
  );
}
