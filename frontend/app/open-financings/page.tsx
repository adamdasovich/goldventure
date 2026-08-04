import OpenFinancingsClient, {
  type OpenFinancingsResponse,
} from "./OpenFinancingsClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

// Open financings turn over slowly; a 5-min ISR window keeps the crawlable
// preview list (company names, financing types) fresh in the initial HTML.
// The client re-fetches on mount for logged-in users to unlock their rows.
export const revalidate = 300;

export default async function OpenFinancingsPage() {
  let initialData: OpenFinancingsResponse | null = null;

  try {
    // Anonymous default-sorted fetch — matches the client's initial filters, so
    // the server-seeded rows line up with what the client would request first.
    const res = await fetch(
      `${API_BASE_URL}/open-financings/?sort_by=announced_date&sort_order=desc`,
      { next: { revalidate: 300 } },
    );
    if (res.ok) {
      initialData = await res.json();
    }
  } catch {
    // Fall back to the client-side fetch in OpenFinancingsClient.
  }

  return <OpenFinancingsClient initialData={initialData} />;
}
