import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SiteNav from "@/components/SiteNav";
import { companyHref } from "@/lib/companyUrl";

const BASE = "https://juniorminingintelligence.com";
const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export const revalidate = 3600;

interface FinancingItem {
  financing_id: number;
  company_id: number;
  company_slug?: string | null;
  company_name: string;
  ticker: string | null;
  financing_type: string;
  status: string | null;
  announced_date: string;
  amount_raised_usd: number;
  lead_agent: string | null;
  press_release_url: string | null;
  primary_commodity: string | null;
}

interface WeekDetail {
  week_ending: string;
  window_start: string | null;
  window_end: string | null;
  count: number;
  total_amount_usd: number;
  by_type: { type: string; count: number; amount_usd: number }[];
  by_commodity: { commodity: string; count: number; amount_usd: number }[];
  items: FinancingItem[];
}

async function fetchWeek(weekEnding: string): Promise<WeekDetail | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/reports/financings/${weekEnding}/`,
      { next: { revalidate: 3600 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as WeekDetail;
  } catch {
    return null;
  }
}

async function fetchWeekList(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/reports/financings/`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.weeks || []).map(
      (w: { week_ending: string }) => w.week_ending,
    );
  } catch {
    return [];
  }
}

function formatWeekEnding(iso: string): string {
  const d = new Date(`${iso}T12:00:00Z`);
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}

function formatUSD(amount: number, compact = true): string {
  if (!amount) return "—";
  if (compact && amount >= 1_000_000)
    return `$${(amount / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 1 })}M`;
  if (compact && amount >= 1_000)
    return `$${(amount / 1_000).toLocaleString("en-US", { maximumFractionDigits: 0 })}K`;
  return `$${amount.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function titleCase(s: string | null): string {
  if (!s) return "—";
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export async function generateStaticParams() {
  const weeks = await fetchWeekList();
  return weeks.map((week_ending) => ({ week_ending }));
}

type Props = { params: Promise<{ week_ending: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { week_ending } = await params;
  const week = await fetchWeek(week_ending);
  const canonical = `${BASE}/reports/financings/${week_ending}`;

  if (!week || week.count === 0) {
    return {
      title: "Financing Roundup Not Found",
      alternates: { canonical },
      robots: { index: false, follow: true },
    };
  }

  const dateLabel = formatWeekEnding(week.week_ending);
  const title = `Junior Mining Financings — Week of ${dateLabel}: ${formatUSD(week.total_amount_usd)} Across ${week.count} Deals`;
  const description = `${week.count} junior mining financings totalling ${formatUSD(week.total_amount_usd, false)} were announced in the week ending ${dateLabel} — private placements, bought deals and flow-through raises across gold, silver, copper, lithium and critical minerals.`;

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      type: "article",
      url: canonical,
      siteName: "Junior Mining Intelligence",
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/og-image.png"],
    },
  };
}

export default async function FinancingRoundupPage({ params }: Props) {
  const { week_ending } = await params;
  const week = await fetchWeek(week_ending);
  if (!week) notFound();

  const canonical = `${BASE}/reports/financings/${week_ending}`;
  const dateLabel = formatWeekEnding(week.week_ending);
  const biggest = week.items[0]; // API returns items sorted by amount desc

  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: `Junior Mining Financings — Week of ${dateLabel}`,
    description: `${week.count} junior mining financings totalling ${formatUSD(week.total_amount_usd, false)} announced in the week ending ${dateLabel}.`,
    datePublished: week.week_ending,
    dateModified: week.week_ending,
    author: {
      "@type": "Organization",
      name: "Junior Mining Intelligence",
      url: BASE,
    },
    publisher: {
      "@type": "Organization",
      name: "Junior Mining Intelligence",
      logo: { "@type": "ImageObject", url: `${BASE}/logo.png` },
    },
    mainEntityOfPage: { "@type": "WebPage", "@id": canonical },
    about: [
      { "@type": "Thing", name: "Junior Mining Financing" },
      { "@type": "Thing", name: "Private Placement" },
    ],
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE },
      {
        "@type": "ListItem",
        position: 2,
        name: "Financing Roundup",
        item: `${BASE}/reports/financings`,
      },
      {
        "@type": "ListItem",
        position: 3,
        name: `Week of ${dateLabel}`,
        item: canonical,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <SiteNav />
      <main className="mx-auto max-w-5xl px-4 py-10 sm:py-14">
        <nav className="mb-6 text-sm text-slate-500">
          <Link href="/" className="hover:text-amber-800">
            Home
          </Link>
          <span className="mx-2">/</span>
          <Link href="/reports/financings" className="hover:text-amber-800">
            Financing Roundup
          </Link>
          <span className="mx-2">/</span>
          <span className="text-slate-700">Week of {dateLabel}</span>
        </nav>

        <header className="mb-8 border-b border-amber-700/40 pb-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
            Weekly Financing Roundup
          </p>
          <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            Junior Mining Financings — Week of {dateLabel}
          </h1>
          {week.count === 0 ? (
            <p className="mt-3 text-base text-slate-600">
              No financings were tracked in this window.
            </p>
          ) : (
            <p className="mt-3 max-w-3xl text-base leading-relaxed text-slate-600">
              Junior mining companies announced{" "}
              <strong className="text-slate-900">{week.count}</strong> financing
              {week.count === 1 ? "" : "s"} totalling{" "}
              <strong className="text-slate-900">
                {formatUSD(week.total_amount_usd, false)}
              </strong>{" "}
              in the week ending {dateLabel}
              {biggest && biggest.amount_raised_usd > 0 ? (
                <>
                  , led by {biggest.company_name}
                  {biggest.ticker ? ` (${biggest.ticker})` : ""} at{" "}
                  {formatUSD(biggest.amount_raised_usd, false)}
                </>
              ) : null}
              . Below is the full breakdown by structure, commodity, and
              company.
            </p>
          )}
        </header>

        {week.count > 0 && (
          <>
            {/* Summary stat cards */}
            <div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Total Raised
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {formatUSD(week.total_amount_usd)}
                </p>
              </div>
              <div className="rounded border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Financings
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {week.count}
                </p>
              </div>
              <div className="rounded border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Biggest Raise
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {biggest ? formatUSD(biggest.amount_raised_usd) : "—"}
                </p>
              </div>
            </div>

            {/* Breakdowns */}
            <div className="mb-10 grid grid-cols-1 gap-8 md:grid-cols-2">
              {week.by_commodity.length > 0 && (
                <section>
                  <h2 className="mb-3 text-xl font-bold text-slate-900">
                    By commodity
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full border border-slate-200 text-sm">
                      <thead className="bg-slate-50 text-left text-slate-600">
                        <tr>
                          <th className="border-b border-slate-200 px-3 py-2">
                            Commodity
                          </th>
                          <th className="border-b border-slate-200 px-3 py-2">
                            Deals
                          </th>
                          <th className="border-b border-slate-200 px-3 py-2 text-right">
                            Raised
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {week.by_commodity
                          .slice()
                          .sort((a, b) => b.amount_usd - a.amount_usd)
                          .map((row) => (
                            <tr key={row.commodity}>
                              <td className="border-b border-slate-100 px-3 py-2 text-slate-800">
                                {titleCase(row.commodity)}
                              </td>
                              <td className="border-b border-slate-100 px-3 py-2 text-slate-600">
                                {row.count}
                              </td>
                              <td className="border-b border-slate-100 px-3 py-2 text-right text-slate-800">
                                {formatUSD(row.amount_usd)}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {week.by_type.length > 0 && (
                <section>
                  <h2 className="mb-3 text-xl font-bold text-slate-900">
                    By financing type
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full border border-slate-200 text-sm">
                      <thead className="bg-slate-50 text-left text-slate-600">
                        <tr>
                          <th className="border-b border-slate-200 px-3 py-2">
                            Type
                          </th>
                          <th className="border-b border-slate-200 px-3 py-2">
                            Deals
                          </th>
                          <th className="border-b border-slate-200 px-3 py-2 text-right">
                            Raised
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {week.by_type
                          .slice()
                          .sort((a, b) => b.amount_usd - a.amount_usd)
                          .map((row) => (
                            <tr key={row.type}>
                              <td className="border-b border-slate-100 px-3 py-2 text-slate-800">
                                {titleCase(row.type)}
                              </td>
                              <td className="border-b border-slate-100 px-3 py-2 text-slate-600">
                                {row.count}
                              </td>
                              <td className="border-b border-slate-100 px-3 py-2 text-right text-slate-800">
                                {formatUSD(row.amount_usd)}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
            </div>

            {/* Full list */}
            <section>
              <h2 className="mb-3 text-xl font-bold text-slate-900">
                All financings this week
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full border border-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-slate-600">
                    <tr>
                      <th className="border-b border-slate-200 px-3 py-2">
                        Company
                      </th>
                      <th className="border-b border-slate-200 px-3 py-2">
                        Type
                      </th>
                      <th className="border-b border-slate-200 px-3 py-2">
                        Commodity
                      </th>
                      <th className="border-b border-slate-200 px-3 py-2 text-right">
                        Amount
                      </th>
                      <th className="border-b border-slate-200 px-3 py-2">
                        Announced
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {week.items.map((item) => (
                      <tr key={item.financing_id} className="align-top">
                        <td className="border-b border-slate-100 px-3 py-2">
                          <Link
                            href={companyHref({
                              id: item.company_id,
                              slug: item.company_slug,
                            })}
                            className="font-medium text-amber-800 hover:underline"
                          >
                            {item.company_name}
                          </Link>
                          {item.ticker && (
                            <span className="ml-1 text-xs text-slate-500">
                              {item.ticker}
                            </span>
                          )}
                          {item.press_release_url && (
                            <a
                              href={item.press_release_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="ml-2 text-xs text-slate-400 hover:text-amber-700"
                            >
                              (release)
                            </a>
                          )}
                        </td>
                        <td className="border-b border-slate-100 px-3 py-2 text-slate-700">
                          {titleCase(item.financing_type)}
                        </td>
                        <td className="border-b border-slate-100 px-3 py-2 text-slate-700">
                          {titleCase(item.primary_commodity)}
                        </td>
                        <td className="border-b border-slate-100 px-3 py-2 text-right text-slate-800">
                          {formatUSD(item.amount_raised_usd)}
                        </td>
                        <td className="border-b border-slate-100 px-3 py-2 text-slate-600">
                          {item.announced_date}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        <footer className="mt-12 border-t border-slate-200 pt-6 text-sm text-slate-500">
          <Link
            href="/reports/financings"
            className="text-amber-800 hover:underline"
          >
            ← All weekly financing roundups
          </Link>
          <span className="mx-2">·</span>
          Amounts are approximate USD equivalents. See{" "}
          <Link
            href="/open-financings"
            className="text-amber-800 hover:underline"
          >
            live open financings
          </Link>{" "}
          for deals still accepting subscriptions.
        </footer>
      </main>
    </>
  );
}
