import { notFound } from "next/navigation";
import CompanyDetailClient from "./CompanyDetailClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateStaticParams() {
  try {
    let allIds: { id: string }[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const res = await fetch(
        `${API_BASE_URL}/companies/?page=${page}&page_size=100`,
      );
      if (!res.ok) break;
      const data = await res.json();
      const results = data.results || [];
      allIds = [...allIds, ...results.map((c: any) => ({ id: String(c.id) }))];
      hasMore = !!data.next;
      page++;
    }

    return allIds;
  } catch {
    return [];
  }
}

export const revalidate = 3600; // ISR: revalidate every hour

export default async function CompanyDetailPage({ params }: Props) {
  const { id } = await params;

  try {
    const [companyRes, projectsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${id}/`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/companies/${id}/projects/`, {
        next: { revalidate: 3600 },
      }),
    ]);

    if (!companyRes.ok) {
      notFound();
    }

    const company = await companyRes.json();
    const projects = projectsRes.ok ? await projectsRes.json() : [];

    return (
      <CompanyDetailClient
        initialCompany={company}
        initialProjects={
          Array.isArray(projects) ? projects : projects.results || []
        }
      />
    );
  } catch {
    notFound();
  }
}
