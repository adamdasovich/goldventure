import { notFound } from "next/navigation";
import CompanyDetailClient from "./CompanyDetailClient";
import { parseCompanyIdParam } from "@/lib/companyUrl";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateStaticParams() {
  try {
    let allParams: { id: string }[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const res = await fetch(
        `${API_BASE_URL}/companies/?page=${page}&page_size=100`,
      );
      if (!res.ok) break;
      const data = await res.json();
      const results = data.results || [];
      allParams = [
        ...allParams,
        ...results
          .filter((c: any) => c.name && (c.description || c.brief_description))
          .map((c: any) => ({
            id: c.slug ? `${c.id}-${c.slug}` : String(c.id),
          })),
      ];
      hasMore = !!data.next;
      page++;
    }

    return allParams;
  } catch {
    return [];
  }
}

export const revalidate = 3600; // ISR: revalidate every hour

export default async function CompanyDetailPage({ params }: Props) {
  const { id: rawSegment } = await params;
  const numericId = parseCompanyIdParam(rawSegment);
  if (numericId === null) notFound();

  // Fetch company + projects + news. notFound() throws NEXT_NOT_FOUND, which
  // must propagate out of any try/catch — so do the fetch outside try, and
  // only guard against genuine network errors.
  let companyRes: Response;
  let projectsRes: Response;
  let newsRes: Response;
  try {
    [companyRes, projectsRes, newsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/projects/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/news-releases/`, {
        next: { revalidate: 1800 },
      }),
    ]);
  } catch {
    notFound();
  }

  if (!companyRes.ok) notFound();

  const company = await companyRes.json();
  const projects = projectsRes.ok ? await projectsRes.json() : [];
  const newsPayload = newsRes.ok
    ? await newsRes.json().catch(() => null)
    : null;
  const newsReleases: any[] = Array.isArray(newsPayload)
    ? newsPayload
    : newsPayload?.results || newsPayload?.news_releases || [];

  // Emit NewsArticle JSON-LD for the 10 most recent press releases so they
  // become eligible for Google's Article rich result + Top Stories indexing.
  const canonicalUrl = `https://juniorminingintelligence.com/companies/${company.id}${company.slug ? `-${company.slug}` : ""}`;
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
    author: {
      "@type": "Organization",
      name: company.name,
    },
    ...(nr.summary && { description: nr.summary.slice(0, 280) }),
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": canonicalUrl,
    },
  }));

  // Canonical URL consolidation happens via <link rel="canonical"> in
  // layout.tsx generateMetadata; HTTP 308 to slug form happens in middleware.ts.

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
      <CompanyDetailClient
        initialCompany={company}
        initialProjects={
          Array.isArray(projects) ? projects : projects.results || []
        }
      />
    </>
  );
}
