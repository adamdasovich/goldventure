import CompaniesClient from "./CompaniesClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export default async function CompaniesPage() {
  let initialCompanies: any[] = [];
  let initialTotalCount = 0;

  try {
    const res = await fetch(`${API_BASE_URL}/companies/?page=1&page_size=9`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const data = await res.json();
      initialCompanies = data.results || [];
      initialTotalCount = data.count || 0;
    }
  } catch {
    // Fall back to client-side fetch
  }

  return (
    <CompaniesClient
      initialCompanies={initialCompanies}
      initialTotalCount={initialTotalCount}
    />
  );
}
