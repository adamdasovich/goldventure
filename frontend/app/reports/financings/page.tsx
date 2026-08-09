import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/SiteNav";

const CANONICAL = "https://juniorminingintelligence.com/reports/financings";
const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Junior Mining Financing Roundup — Weekly Private Placements & Raises",
  description:
    "Weekly roundup of junior mining financings: private placements, bought deals, and flow-through raises across gold, silver, copper, lithium and critical minerals. Amounts raised, deal counts, and the companies behind each raise.",
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: "Weekly Junior Mining Financing Roundup",
    description:
      "Every week's junior mining raises — private placements, bought deals, flow-through — with amounts, deal counts, and the companies behind them.",
    type: "website",
    url: CANONICAL,
    siteName: "Junior Mining Intelligence",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Weekly Junior Mining Financing Roundup",
    description:
      "Junior mining raises each week — private placements, bought deals, flow-through — with amounts and companies.",
    images: ["/og-image.png"],
  },
};

interface WeekSummary {
  week_ending: string;
  generated_at: string | null;
  count: number;
  total_amount_usd: number;
  top_commodity: string | null;
}

async function fetchWeeks(): Promise<WeekSummary[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/reports/financings/`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.weeks || [];
  } catch (error) {
    console.error("Failed to fetch financing roundups:", error);
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

function formatUSD(amount: number): string {
  if (!amount) return "—";
  if (amount >= 1_000_000)
    return `$${(amount / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 1 })}M`;
  if (amount >= 1_000)
    return `$${(amount / 1_000).toLocaleString("en-US", { maximumFractionDigits: 0 })}K`;
  return `$${amount.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

const collectionJsonLd = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Weekly Junior Mining Financing Roundup",
  url: CANONICAL,
  description:
    "Archive of weekly junior mining financing roundups covering private placements, bought deals, and flow-through raises.",
  isPartOf: {
    "@type": "WebSite",
    "@id": "https://juniorminingintelligence.com/#website",
  },
};

export default async function FinancingRoundupArchivePage() {
  const weeks = await fetchWeeks();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionJsonLd) }}
      />
      <SiteNav />
      <main className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
        <header className="mb-10 border-b border-amber-700/40 pb-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
            Financing Roundup
          </p>
          <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            Weekly Junior Mining Financing Roundup
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-600">
            Junior miners fund exploration through the market — private
            placements, bought deals, and flow-through share offerings. Each
            week we round up the raises we&apos;ve tracked across gold, silver,
            copper, lithium, and critical minerals: how much was raised, by
            whom, and in what structure. It&apos;s a fast read on where capital
            is actually flowing in the sector.
          </p>
        </header>

        {weeks.length === 0 ? (
          <div className="rounded border border-slate-200 bg-slate-50 p-6 text-center text-slate-600">
            No financing roundups published yet. Check back after Friday&apos;s
            report generates.
          </div>
        ) : (
          <ul className="space-y-3">
            {weeks.map((week) => (
              <li
                key={week.week_ending}
                className="flex flex-col gap-2 rounded border border-slate-200 bg-white p-5 transition hover:border-amber-700/60 hover:shadow-sm sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <Link
                    href={`/reports/financings/${week.week_ending}`}
                    className="text-lg font-semibold text-slate-900 hover:text-amber-800 hover:underline"
                  >
                    Week ending {formatWeekEnding(week.week_ending)}
                  </Link>
                  <p className="mt-1 text-sm text-slate-600">
                    {week.count} financing{week.count === 1 ? "" : "s"} ·{" "}
                    {formatUSD(week.total_amount_usd)} raised
                    {week.top_commodity
                      ? ` · led by ${week.top_commodity}`
                      : ""}
                  </p>
                </div>
                <Link
                  href={`/reports/financings/${week.week_ending}`}
                  className="self-start rounded bg-amber-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-800 sm:self-auto"
                >
                  View roundup
                </Link>
              </li>
            ))}
          </ul>
        )}

        <footer className="mt-12 border-t border-slate-200 pt-6 text-sm text-slate-500">
          Roundups cover the trailing 7 days through each Friday close. See also
          the{" "}
          <Link
            href="/open-financings"
            className="text-amber-800 hover:underline"
          >
            live open financings
          </Link>{" "}
          and the full{" "}
          <Link
            href="/reports/weekly"
            className="text-amber-800 hover:underline"
          >
            weekly industry report
          </Link>
          .
        </footer>
      </main>
    </>
  );
}
