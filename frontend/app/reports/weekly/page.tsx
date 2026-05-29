import type { Metadata } from "next";
import Link from "next/link";

const CANONICAL = "https://juniorminingintelligence.com/reports/weekly";
const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

// Cache for one hour; the report is generated weekly so this is generous.
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Weekly Mining Industry Report — GoldVenture",
  description:
    "Friday weekly snapshot of junior mining industry activity: top stock moves with catalysts, new NI 43-101 reports, financings closed, metal price changes, and emerging themes.",
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: "Weekly Mining Industry Report",
    description:
      "Top movers with catalysts, new NI 43-101 reports, financings closed, metal prices, emerging themes — every Friday after the close.",
    type: "website",
    url: CANONICAL,
  },
};

interface ReportSummary {
  week_ending: string;
  status: string;
  generated_at: string | null;
  has_pdf: boolean;
  html_url: string;
  pdf_url: string | null;
}

interface ReportListResponse {
  count: number;
  reports: ReportSummary[];
}

async function fetchReports(): Promise<ReportSummary[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/reports/weekly/`, {
      next: { revalidate: 3600 },
    });
    if (!response.ok) return [];
    const data: ReportListResponse = await response.json();
    return data.reports || [];
  } catch (error) {
    console.error("Failed to fetch weekly reports:", error);
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

export default async function WeeklyReportsArchivePage() {
  const reports = await fetchReports();

  return (
    <main className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
      <header className="mb-10 border-b border-amber-700/40 pb-6">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
          Weekly Report Archive
        </p>
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
          Weekly Mining Industry Report
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-600">
          A Friday afternoon snapshot of the junior mining industry — top stock
          moves with catalysts, new NI 43-101 reports, financings closed, metal
          price changes, and emerging themes. Generated automatically after the
          close.
        </p>
      </header>

      {reports.length === 0 ? (
        <div className="rounded border border-slate-200 bg-slate-50 p-6 text-center text-slate-600">
          No reports published yet. Check back after Friday at 5:30 PM ET.
        </div>
      ) : (
        <ul className="space-y-3">
          {reports.map((report) => (
            <li
              key={report.week_ending}
              className="flex flex-col gap-3 rounded border border-slate-200 bg-white p-5 transition hover:border-amber-700/60 hover:shadow-sm sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <Link
                  href={`/reports/weekly/${report.week_ending}`}
                  className="text-lg font-semibold text-slate-900 hover:text-amber-800 hover:underline"
                >
                  Week ending {formatWeekEnding(report.week_ending)}
                </Link>
                {report.generated_at && (
                  <p className="mt-1 text-xs text-slate-500">
                    Generated{" "}
                    {new Date(report.generated_at).toLocaleString("en-US", {
                      dateStyle: "medium",
                      timeStyle: "short",
                      timeZone: "America/New_York",
                    })}{" "}
                    ET
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  href={`/reports/weekly/${report.week_ending}`}
                  className="rounded bg-amber-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-800"
                >
                  Read
                </Link>
                {report.pdf_url && (
                  <a
                    href={report.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
                  >
                    PDF
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <footer className="mt-12 text-center text-xs text-slate-500">
        Reports cover the trailing 7 days through the Friday close.
      </footer>
    </main>
  );
}
