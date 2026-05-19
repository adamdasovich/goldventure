import HomeClient from "./HomeClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export default async function Home() {
  let initialArticles: any[] = [];

  try {
    const res = await fetch(
      `${API_BASE_URL}/news/articles/?limit=50&offset=0&days=7`,
      { cache: "no-store" },
    );
    if (res.ok) {
      const data = await res.json();
      initialArticles = data.articles || [];
    }
  } catch {
    // Fall back to client-side fetch
  }

  return <HomeClient initialArticles={initialArticles} />;
}
