import Link from "next/link";
import { companyHref } from "@/lib/companyUrl";

/**
 * A crawlable A-Z index of every company.
 *
 * /companies server-renders nine companies and its pagination is client state,
 * so the HTML carried nine profile links and no page= links at all. That left
 * 385 profiles discoverable only through the sitemap and the commodity facets
 * -- and a company with no commodity on file appears on no facet, so 32 of
 * them had no internal link pointing at them from anywhere.
 *
 * A sitemap tells a crawler a URL exists. Internal links are what say it
 * matters, and which pages on the site consider it related. Both are needed.
 *
 * The commodity facet pages already render 262 company links each without
 * trouble, so the volume here is not a concern.
 */

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type DirectoryCompany = {
  id: number;
  name: string;
  slug?: string | null;
  ticker_symbol?: string | null;
  exchange?: string | null;
  project_count?: number | null;
};

async function fetchAllCompanies(): Promise<DirectoryCompany[]> {
  let companies: DirectoryCompany[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const url = `${API_BASE_URL}/companies/?page=${page}&page_size=100`;
    let data: any = null;
    // Retry rather than swallow: returning [] on a blip would bake an empty
    // index into the static build and quietly undo the point of the page.
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const res = await fetch(url, { next: { revalidate: 3600 } });
        if (!res.ok) break;
        data = await res.json();
        break;
      } catch {
        if (attempt === 2) break;
        await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
      }
    }
    if (!data) break;

    companies = [...companies, ...(data.results || [])];
    hasMore = !!data.next;
    page++;
  }

  return companies
    .filter((c) => c.name)
    .sort((a, b) => a.name.localeCompare(b.name));
}

/** First character to group under — digits and symbols share one bucket. */
function bucketOf(name: string): string {
  const ch = name.trim().charAt(0).toUpperCase();
  return /[A-Z]/.test(ch) ? ch : "#";
}

export default async function CompanyDirectoryIndex() {
  const companies = await fetchAllCompanies();
  if (companies.length === 0) return null;

  const buckets = new Map<string, DirectoryCompany[]>();
  for (const company of companies) {
    const key = bucketOf(company.name);
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key)!.push(company);
  }
  const letters = [...buckets.keys()].sort((a, b) =>
    a === "#" ? 1 : b === "#" ? -1 : a.localeCompare(b),
  );

  return (
    <section
      id="company-directory"
      className="border-t border-slate-800 bg-slate-900"
      aria-label="Full company directory"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <h2 className="text-2xl font-bold text-gold-400 mb-3">
          All companies A–Z
        </h2>
        <p className="text-slate-400 mb-8 max-w-3xl">
          Every one of the {companies.length} mining companies we track, with a
          direct link to its profile — projects, financings, resource estimates
          and press releases.
        </p>

        <nav aria-label="Jump to letter" className="mb-8 flex flex-wrap gap-2">
          {letters.map((letter) => (
            <a
              key={letter}
              href={`#companies-${letter === "#" ? "0" : letter}`}
              className="px-2.5 py-1 rounded border border-slate-700 text-slate-300 hover:border-gold-500/50 hover:text-gold-300 transition-colors text-sm"
            >
              {letter}
            </a>
          ))}
        </nav>

        <div className="flex flex-col gap-8">
          {letters.map((letter) => (
            <div
              key={letter}
              id={`companies-${letter === "#" ? "0" : letter}`}
              className="scroll-mt-24"
            >
              <h3 className="text-lg font-semibold text-slate-200 mb-3 border-b border-slate-800 pb-1">
                {letter}
              </h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2">
                {buckets.get(letter)!.map((company) => (
                  <li key={company.id} className="text-sm leading-snug">
                    <Link
                      href={companyHref(company)}
                      className="text-slate-300 hover:text-gold-400"
                    >
                      {company.name}
                    </Link>
                    {company.ticker_symbol && (
                      <span className="ml-1.5 text-xs text-slate-500">
                        {company.ticker_symbol}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
