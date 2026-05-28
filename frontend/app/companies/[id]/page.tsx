import { notFound, permanentRedirect } from "next/navigation";
import CompanyDetailClient from "./CompanyDetailClient";
import { companyHref, parseCompanyIdParam } from "@/lib/companyUrl";

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

  try {
    const [companyRes, projectsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${numericId}/projects/`, {
        next: { revalidate: 3600 },
      }),
    ]);

    if (!companyRes.ok) {
      notFound();
    }

    const company = await companyRes.json();
    const projects = projectsRes.ok ? await projectsRes.json() : [];

    // 301 redirect to the canonical slug URL if the URL segment doesn't match.
    const canonicalSegment = company.slug
      ? `${company.id}-${company.slug}`
      : `${company.id}`;
    if (rawSegment !== canonicalSegment) {
      permanentRedirect(companyHref(company));
    }

    return (
      <CompanyDetailClient
        initialCompany={company}
        initialProjects={
          Array.isArray(projects) ? projects : projects.results || []
        }
      />
    );
  } catch (err) {
    // permanentRedirect throws a special NEXT_REDIRECT error — re-throw so the
    // framework can handle it. Anything else means the fetch genuinely failed.
    if (err && typeof err === "object" && "digest" in err) {
      throw err;
    }
    notFound();
  }
}
