import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SiteNav from "@/components/SiteNav";

const SITE_URL = "https://juniorminingintelligence.com";
const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

export const revalidate = 3600;

interface PageProps {
  params: Promise<{ week_ending: string }>;
}

interface ReportSummary {
  week_ending: string;
  status: string;
  has_pdf: boolean;
  html_url: string;
  pdf_url: string | null;
}

async function fetchReport(weekEnding: string): Promise<ReportSummary | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/reports/weekly/`, {
      next: { revalidate: 3600 },
    });
    if (!response.ok) return null;
    const data = await response.json();
    return (
      (data.reports || []).find(
        (r: ReportSummary) => r.week_ending === weekEnding,
      ) || null
    );
  } catch (error) {
    console.error("Failed to fetch weekly report metadata:", error);
    return null;
  }
}

function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s));
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

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { week_ending } = await params;
  if (!isValidDate(week_ending)) return {};

  const canonical = `${SITE_URL}/reports/weekly/${week_ending}`;
  const title = `Weekly Mining Industry Report — Week ending ${formatWeekEnding(week_ending)}`;
  const description =
    "Junior mining weekly: top movers with catalysts, new NI 43-101 reports, financings closed, metal price changes, and emerging themes.";

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: { title, description, type: "article", url: canonical },
  };
}

export default async function WeeklyReportDetailPage({ params }: PageProps) {
  const { week_ending } = await params;
  if (!isValidDate(week_ending)) notFound();

  const report = await fetchReport(week_ending);
  if (!report) notFound();

  // The Django HTML endpoint returns a fully-formed document. Iframe-embed it
  // so the report's print-styled CSS stays isolated from the site theme.
  const iframeSrc = `${API_BASE_URL}/reports/weekly/${week_ending}/`;

  return (
    <>
      <SiteNav />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link
              href="/reports/weekly"
              className="text-sm font-medium text-amber-700 hover:text-amber-800 hover:underline"
            >
              &larr; All weekly reports
            </Link>
            <h1 className="mt-2 text-2xl font-bold text-slate-900">
              Week ending {formatWeekEnding(week_ending)}
            </h1>
          </div>
          <div className="flex gap-2">
            {report.pdf_url && (
              <a
                href={report.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
              >
                Download PDF
              </a>
            )}
            <a
              href={report.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded bg-amber-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-800"
            >
              Open in new tab
            </a>
          </div>
        </div>

        <div className="overflow-hidden rounded border border-slate-200 bg-white shadow-sm">
          <iframe
            src={iframeSrc}
            title={`Weekly mining report — week ending ${week_ending}`}
            className="block h-[1400px] w-full"
            loading="lazy"
          />
        </div>
      </main>
    </>
  );
}
