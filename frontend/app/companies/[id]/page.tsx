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

  // Fetch company + projects. notFound() throws NEXT_NOT_FOUND, which must
  // propagate out of any try/catch — so do the fetch outside try, and only
  // guard against genuine network errors.
  let companyRes: Response;
  let projectsRes: Response;
  try {
    [companyRes, projectsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/projects/`, {
        next: { revalidate: 3600 },
      }),
    ]);
  } catch {
    notFound();
  }

  if (!companyRes.ok) notFound();

  const company = await companyRes.json();
  const projects = projectsRes.ok ? await projectsRes.json() : [];

  // Canonical URL consolidation happens via <link rel="canonical"> in
  // layout.tsx generateMetadata — Next.js 16 cache components prevent
  // permanentRedirect() from emitting a 308 here. Google honors rel=canonical
  // for ranking-signal consolidation, so the SEO outcome is equivalent.

  return (
    <CompanyDetailClient
      initialCompany={company}
      initialProjects={
        Array.isArray(projects) ? projects : projects.results || []
      }
    />
  );
}
