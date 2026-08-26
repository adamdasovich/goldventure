import CompaniesClient from "./CompaniesClient";
import CompanyDirectoryIndex from "./CompanyDirectoryIndex";
import { fetchSignupOffer } from "@/lib/signupOffer";

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

  // Read server-side so the CTA copy is correct in the first paint. Paid search
  // traffic should never see the wrong offer flash and then change.
  const signupOffer = await fetchSignupOffer();

  return (
    <>
      <CompaniesClient
        initialCompanies={initialCompanies}
        initialTotalCount={initialTotalCount}
        signupOffer={signupOffer}
      />
      {/*
        The grid above server-renders nine companies and paginates in client
        state, so the HTML carried nine profile links and no page= links.
        This is what actually makes 385 profiles reachable by internal link
        rather than by sitemap alone.
      */}
      <CompanyDirectoryIndex />
    </>
  );
}
