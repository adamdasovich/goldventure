import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import SiteHeader from "@/components/SiteHeader";
import DrillScannerClient from "./DrillScannerClient";
import { toolBySlug } from "../tools";

const BASE = "https://juniorminingintelligence.com";

// Metadata + canonical live in layout.tsx.
export const revalidate = 3600;

/**
 * Server-rendered shell for the Drill Result Scanner.
 *
 * The page used to be a single "use client" component rendering 86 words —
 * a heading and a tool, with nothing a search engine could index. Google
 * filed it as a soft 404, which is the correct call for a page carrying no
 * content. The interactive scanner now lives in DrillScannerClient; the
 * explanatory content below renders into the HTML for every visitor.
 *
 * Everything in "Method and limitations" is checked against the endpoint in
 * backend/core/views/investor_tools.py::drill_scanner — the keyword list, the
 * 90-day ceiling, the 50-result cap, and the fact that the most-active
 * ranking is computed from that capped window rather than the full match set.
 */

const RELATED = ["catalyst-calendar", "signal-to-noise", "resource-growth"];

const FAQS = [
  {
    q: "What counts as a good drill intercept?",
    a: "There is no universal threshold, because grade only means something alongside width and depth. A useful shorthand is grade multiplied by width — a gram-metre figure — which lets you compare a narrow high-grade hit against a broad low-grade one. For gold, anything sustained above roughly 5 g/t over meaningful width is high grade, 1–5 g/t is typical of open-pit material, and below 1 g/t needs bulk tonnage and favourable economics to matter.",
  },
  {
    q: "Why do some drill results look impressive but move the share price very little?",
    a: "Usually because the interval is a down-hole width rather than a true width, because it sits far from existing infrastructure or resources, or because the market already expected it. A single spectacular hole in isolation also carries far less weight than a pattern of consistent intercepts that can support a resource estimate.",
  },
  {
    q: "How often is the scanner updated?",
    a: "Company news is re-scraped every morning, so releases appear within a day of publication. The scanner reads the releases already in the database rather than searching the web live.",
  },
  {
    q: "Does the scanner interpret the assay numbers for me?",
    a: "No. It finds and surfaces the releases that report drilling; reading the intervals is still your job. The guide to interpreting drill results covers grade times width, true versus down-hole width, and the presentation tricks worth watching for.",
  },
];

export default function DrillScannerPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE },
      {
        "@type": "ListItem",
        position: 2,
        name: "Investor Tools",
        item: `${BASE}/investor-tools`,
      },
      {
        "@type": "ListItem",
        position: 3,
        name: "Drill Result Scanner",
        item: `${BASE}/investor-tools/drill-scanner`,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />

      {/* Nav */}
      <SiteHeader />

      {/* Header */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-3">
            Exploration Tool
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-3">
            Drill Result Scanner
          </h1>
          <p className="text-slate-300 max-w-2xl mx-auto">
            Search every junior mining press release for drill results and
            assays in one place, filter by commodity and period, and see which
            companies are drilling hardest right now.
          </p>
        </div>
      </section>

      {/* The tool itself */}
      <DrillScannerClient />

      {/* ================= Explanatory content ================= */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex flex-col gap-14 border-t border-slate-800 pt-14">
        <section id="what-it-does">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            What this tool does
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            <p>
              Drill results are the primary catalyst in junior mining. An
              exploration company has no revenue and often no mine, so what
              moves its share price is evidence that there is something in the
              ground — and that evidence arrives as assay results in press
              releases, a few companies at a time, scattered across hundreds of
              corporate websites.
            </p>
            <p>
              The scanner reads the press releases already collected from every
              company we track and surfaces the ones reporting drilling. Rather
              than checking company sites one by one, you get a single feed of
              recent exploration results, filterable by commodity and by period,
              alongside a ranking of which companies have been most active.
            </p>
            <p>
              That second part is the less obvious use. A company releasing
              drill results repeatedly is one with a rig turning and a budget to
              pay for it. A long silence usually means the opposite — the
              programme has ended, the results were not worth announcing, or the
              treasury is empty and a{" "}
              <Link
                href="/guides/how-junior-mining-companies-raise-money"
                className="text-gold-400 hover:underline"
              >
                financing
              </Link>{" "}
              is coming.
            </p>
          </div>
        </section>

        <section id="how-to-read">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            How to read the output
          </h2>
          <div className="flex flex-col gap-5">
            <div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">
                The results feed
              </h3>
              <p className="text-slate-300 leading-relaxed">
                Each row is a single press release: the company, its ticker, the
                headline, and the publication date, linking to the original
                release on the company&apos;s own site. Read the original — the
                headline is written to sell, and the interval that matters is
                usually further down.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">
                Most active drillers
              </h3>
              <p className="text-slate-300 leading-relaxed">
                A count of how many drilling releases each company published
                within the results shown. Treat it as a measure of recent
                cadence, not of programme size — a company running one large rig
                and reporting quarterly will rank below one issuing frequent
                small updates.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">
                Period and commodity filters
              </h3>
              <p className="text-slate-300 leading-relaxed">
                Shorter windows show what is happening now; 90 days smooths out
                the seasonality of drilling, which in much of Canada is
                concentrated in the months when the ground is accessible. The
                commodity filter works from each company&apos;s project data
                rather than the text of the release.
              </p>
            </div>
          </div>
        </section>

        <section id="what-good-looks-like">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            What good looks like
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            <p>
              Grade on its own tells you very little. A headline reading
              &ldquo;15 g/t gold&rdquo; is meaningless until you know over what
              width and at what depth. The usual shorthand is grade multiplied
              by width — gram-metres — which lets a narrow high-grade hit be
              compared against a broad lower-grade one.
            </p>
            <p>
              As rough orientation for gold: sustained intervals above about 5
              g/t are high grade, 1–5 g/t is the range most open-pit deposits
              live in, and below 1 g/t needs real tonnage and favourable
              economics to be worth mining. Copper is quoted as a percentage
              instead, where anything above roughly 1% Cu is strong for a
              porphyry.
            </p>
            <p>
              The pattern matters more than any single hole. One exceptional
              intercept can be an isolated pocket; a series of consistent ones
              across a defined zone is what eventually supports a resource
              estimate. Watch for true width versus down-hole width — a hole
              drilled obliquely through a structure overstates the interval, and
              releases do not always make the distinction obvious.
            </p>
            <p className="text-slate-400">
              Our{" "}
              <Link
                href="/guides/how-to-interpret-mining-drill-results"
                className="text-gold-400 hover:underline"
              >
                guide to interpreting drill results
              </Link>{" "}
              works through grade tiers by metal, true versus down-hole width,
              and ten presentation tricks worth recognising. For the grade
              fundamentals see{" "}
              <Link
                href="/guides/gold-grade-explained"
                className="text-gold-400 hover:underline"
              >
                gold grade explained
              </Link>
              .
            </p>
          </div>
        </section>

        <section id="method">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            Method and limitations
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            <p>
              The scanner matches press release <strong>titles</strong> against
              a keyword list covering drilling and assay vocabulary — drill,
              assay, intercept, metres, g/t, mineralization, hole, core,
              sampling, trench, channel sample and related terms. Matching is
              case-insensitive.
            </p>
            <p>
              Three limitations follow directly from that design, and they are
              worth knowing before you rely on the output:
            </p>
            <ul className="list-disc pl-6 flex flex-col gap-3 text-slate-300">
              <li>
                <strong className="text-slate-100">
                  Titles only, not full text.
                </strong>{" "}
                A company that publishes assays under a generic headline such as
                &ldquo;Exploration Update&rdquo; will not appear. This is the
                most likely reason a release you expected to see is missing.
              </li>
              <li>
                <strong className="text-slate-100">
                  Keyword matching produces false positives.
                </strong>{" "}
                Words like &ldquo;core&rdquo; and &ldquo;hole&rdquo; appear in
                non-geological contexts, so the occasional unrelated release
                surfaces.
              </li>
              <li>
                <strong className="text-slate-100">
                  The feed is capped at the 50 most recent matches,
                </strong>{" "}
                and the most-active ranking is counted from those 50 rather than
                from every matching release in the period. Over a busy 90-day
                window the ranking therefore reflects the most recent activity,
                not the full quarter.
              </li>
            </ul>
            <p>
              The period is capped at 90 days. Company news is re-scraped daily,
              so releases generally appear within a day of publication, and the
              scanner searches stored releases rather than the live web.
            </p>
          </div>
        </section>

        <section id="related">
          <h2 className="text-2xl font-bold text-gold-400 mb-5">
            Related tools
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {RELATED.map((slug) => {
              const tool = toolBySlug(slug);
              if (!tool) return null;
              return (
                <Link
                  key={slug}
                  href={tool.href}
                  className="glass-card rounded-xl p-5 border border-slate-700 hover:border-gold-400/30 transition-colors"
                >
                  <h3 className="text-base font-semibold text-slate-100 mb-2">
                    {tool.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {tool.description}
                  </p>
                </Link>
              );
            })}
          </div>
          <p className="text-slate-400 mt-6 leading-relaxed">
            Drilling cadence is one input. Pair it with the{" "}
            <Link
              href="/investor-tools/signal-to-noise"
              className="text-gold-400 hover:underline"
            >
              Signal-to-Noise Ratio
            </Link>{" "}
            to see what share of a company&apos;s announcements report results
            at all, and browse{" "}
            <Link
              href="/companies/commodity/gold"
              className="text-gold-400 hover:underline"
            >
              gold companies
            </Link>{" "}
            or{" "}
            <Link
              href="/investor-tools"
              className="text-gold-400 hover:underline"
            >
              all investor tools
            </Link>
            .
          </p>
        </section>

        <section id="faq">
          <h2 className="text-2xl font-bold text-gold-400 mb-5">
            Frequently asked questions
          </h2>
          <div className="flex flex-col gap-5">
            {FAQS.map((f) => (
              <div key={f.q} className="glass-card rounded-xl p-5">
                <h3 className="text-base font-semibold text-slate-100 mb-2">
                  {f.q}
                </h3>
                <p className="text-slate-300 leading-relaxed">{f.a}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
