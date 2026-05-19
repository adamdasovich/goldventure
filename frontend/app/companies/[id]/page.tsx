import { notFound } from "next/navigation";
import CompanyDetailClient from "./CompanyDetailClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function CompanyDetailPage({ params }: Props) {
  const { id } = await params;

  try {
    const [companyRes, projectsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/companies/${id}/`, { cache: "no-store" }),
      fetch(`${API_BASE_URL}/companies/${id}/projects/`, { cache: "no-store" }),
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
