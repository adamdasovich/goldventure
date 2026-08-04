import MetalsClient from "./MetalsClient";
import type { MetalPrice } from "@/lib/api";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

// Metals are scraped a few times a day; a 15-min ISR window keeps the
// server-rendered prices fresh for crawlers without hammering the API. The
// client re-fetches live data on mount regardless.
export const revalidate = 900;

export default async function MetalsPage() {
  let initialMetals: MetalPrice[] = [];
  let initialTimestamp = "";

  try {
    const res = await fetch(`${API_BASE_URL}/metals/prices/`, {
      next: { revalidate: 900 },
    });
    if (res.ok) {
      const data = await res.json();
      initialMetals = data.metals || [];
      initialTimestamp = data.timestamp || "";
    }
  } catch {
    // Fall back to the client-side fetch in MetalsClient.
  }

  return (
    <MetalsClient
      initialMetals={initialMetals}
      initialTimestamp={initialTimestamp}
    />
  );
}
