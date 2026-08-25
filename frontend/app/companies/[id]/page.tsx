import { notFound } from "next/navigation";
import CompanyDetailClient from "./CompanyDetailClient";
import CompanyProfileContent from "./CompanyProfileContent";
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
        // Every real company is prerendered, not just the ones thick enough
        // to index. With dynamicParams disabled, anything left out of this
        // list 404s -- and a thin-but-real company should still have a page.
        // Whether it is indexed is layout.tsx's decision, separately.
        ...results
          .filter((c: any) => c.name)
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

// Anything outside generateStaticParams 404s at the router instead of being
// rendered. notFound() alone could not do this: with dynamic params enabled
// Next serves an ISR shell for an unknown id and answers HTTP 200, so
// /companies/<anything> read as a soft 404 over an unbounded URL space, and a
// deleted company left a live-looking page behind.
export const dynamicParams = false;

export const revalidate = 3600;

export default async function CompanyDetailPage({ params }: Props) {
  const { id: rawSegment } = await params;
  const numericId = parseCompanyIdParam(rawSegment);
  if (numericId === null) notFound();

  let companyRes: Response;
  let projectsRes: Response;
  let newsRes: Response | null = null;
  try {
    [companyRes, projectsRes, newsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/projects/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/news-releases/`, {
        next: { revalidate: 3600 },
      }),
    ]);
  } catch {
    notFound();
  }

  if (!companyRes.ok) notFound();

  const company = await companyRes.json();
  const projects = projectsRes.ok ? await projectsRes.json() : [];
  const projectList: any[] = Array.isArray(projects)
    ? projects
    : projects.results || [];

  // The news endpoint splits releases into financial / non-financial buckets;
  // the profile summary wants them merged and date-sorted.
  let news: any[] = [];
  if (newsRes?.ok) {
    try {
      const payload = await newsRes.json();
      news = Array.isArray(payload)
        ? payload
        : [...(payload.financial || []), ...(payload.non_financial || [])];
    } catch {
      news = [];
    }
  }

  // BreadcrumbList + NewsArticle JSON-LD are emitted from layout.tsx —
  // see comment there for the Next.js 16 RSC streaming caveat.

  return (
    <>
      <CompanyDetailClient
        initialCompany={company}
        initialProjects={projectList}
      />
      {/*
        Server-rendered facts below the interactive tabs. The tabs are a client
        component, so until now every profile shipped roughly 250 crawlable
        words no matter how much data sat behind it.
      */}
      <CompanyProfileContent
        company={company}
        projects={projectList}
        news={news}
      />
    </>
  );
}
