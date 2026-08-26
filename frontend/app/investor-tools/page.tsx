import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import SiteHeader from "@/components/SiteHeader";
import ToolsGrid from "./ToolsGrid";
import {
  AVAILABLE_COUNT,
  FREE_TOOL_SLUGS,
  PROSPECTOR_COUNT,
  QUESTION_MAP,
  TOOL_GROUPS,
  toolBySlug,
} from "./tools";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const BASE = "https://juniorminingintelligence.com";

// Metadata + canonical live in layout.tsx.
export const revalidate = 3600;

/**
 * Headline figures quoted in the methodology copy.
 *
 * Fetched rather than hardcoded: these are the numbers that make the page
 * worth linking to, and a stale statistic is worse than none. Falls back to
 * prose that reads correctly without them if the API is unreachable, so a
 * failed fetch degrades the page rather than breaking it.
 */
async function getSectorStats() {
  const stats: {
    illiquidCount: number | null;
    liquidityUniverse: number | null;
    medianDollarVolume: number | null;
    signalPct: number | null;
    totalReleases: number | null;
  } = {
    illiquidCount: null,
    liquidityUniverse: null,
    medianDollarVolume: null,
    signalPct: null,
    totalReleases: null,
  };

  try {
    const [liq, sig] = await Promise.all([
      fetch(`${API_BASE_URL}/tools/liquidity-screener/?position=25000`, {
        next: { revalidate: 3600 },
      }),
      fetch(`${API_BASE_URL}/tools/signal-to-noise/`, {
        next: { revalidate: 3600 },
      }),
    ]);

    if (liq.ok) {
      const s = (await liq.json())?.summary;
      if (s) {
        stats.illiquidCount = s.under_5k ?? null;
        stats.liquidityUniverse = s.companies ?? null;
        stats.medianDollarVolume = s.median_daily_dollar_volume ?? null;
      }
    }
    if (sig.ok) {
      const s = (await sig.json())?.summary;
      if (s) {
        stats.signalPct = s.sector_signal_pct ?? null;
        stats.totalReleases = s.total_releases ?? null;
      }
    }
  } catch {
    // Keep the nulls; the copy below reads fine without the figures.
  }

  return stats;
}

const FAQS = [
  {
    q: "Which investor tools are free?",
    a: `${FREE_TOOL_SLUGS.length} of the ${AVAILABLE_COUNT} tools are open to anyone without an account: the Resource Grade Ranker and the Sector Pulse Dashboard. A Prospector subscription unlocks ${PROSPECTOR_COUNT}, and Miner adds the Warrant Overhang Radar on top.`,
  },
  {
    q: "What is a good EV per ounce for a junior mining company?",
    a: "It depends almost entirely on stage and jurisdiction, which is why the figure is only useful against comparables rather than as an absolute. An explorer with an inferred resource in a difficult jurisdiction trades at a small fraction of a permitted developer in a stable one. The Peer Comparison Engine benchmarks a company against automatically detected peers so the number has a reference point.",
  },
  {
    q: "What does warrant overhang mean?",
    a: "Warrants issued in past financings give holders the right to buy new shares at a fixed strike price. While the share price sits below that strike they are largely dormant; once it rises above, exercise becomes likely, which issues new shares and dilutes existing holders — often capping the rally that triggered it. The Warrant Overhang Radar shows the strike prices, the resulting share count, and the expiry dates.",
  },
  {
    q: "How do you measure whether a mining company is actually exploring?",
    a: "By classifying every press release and measuring what share of them report a genuine result — drill intercepts, resource updates, or study results — as opposed to corporate housekeeping such as grants, appointments and conference attendance. The Signal-to-Noise Ratio tool reports that share per company against the sector norm.",
  },
  {
    q: "Why does liquidity matter so much for junior mining stocks?",
    a: "Because the exit is the part most retail investors never model. A great many junior listings trade so little value per day that an ordinary position cannot be sold in any reasonable time without moving the price against you. That risk does not appear on a conventional screener, so the Liquidity & Days to Exit tool measures it directly from trading history.",
  },
  {
    q: "Where does the underlying data come from?",
    a: "Resource figures, grades and economic studies are taken from filed NI 43-101 technical reports. Financing and warrant terms come from company announcements. Prices and volumes come from exchange market data, and company news is re-scraped from company websites every morning.",
  },
];

export default async function InvestorToolsPage() {
  const stats = await getSectorStats();

  const illiquidPct =
    stats.illiquidCount && stats.liquidityUniverse
      ? Math.round((stats.illiquidCount / stats.liquidityUniverse) * 100)
      : null;

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
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-4xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Investor Intelligence
          </Badge>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-slate-50 mb-5 tracking-tight">
            Junior Mining Investor Tools
          </h1>
          <p className="text-lg text-slate-300 leading-relaxed">
            {AVAILABLE_COUNT} purpose-built analytics tools for junior mining
            investors — screening, valuation, capital structure, and the two
            risks conventional screeners leave out: whether you could sell, and
            whether the company is doing anything.
          </p>
          <p className="text-slate-400 mt-4 leading-relaxed">
            Every figure is computed from filed NI 43-101 technical reports,
            company financing announcements, and exchange market data across the
            companies we track. The methodology is published below.
          </p>
          <div className="mt-6">
            <Link href="/pricing">
              <Badge
                variant="slate"
                className="cursor-pointer hover:border-gold-400/50"
              >
                {FREE_TOOL_SLUGS.length} tools free &middot; all{" "}
                {AVAILABLE_COUNT} from Prospector
              </Badge>
            </Link>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 flex flex-col gap-20">
        {/* ============ Which tool answers which question ============ */}
        <section id="which-tool" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-4">
            Which tool answers which question
          </h2>
          <p className="text-slate-300 leading-relaxed max-w-3xl mb-8">
            Most analysis starts with a specific worry rather than a metric.
            These are the questions investors actually bring to a junior, and
            where each one gets answered.
          </p>

          <div className="flex flex-col gap-6">
            {QUESTION_MAP.map((row) => (
              <div
                key={row.question}
                className="glass-card rounded-xl p-5 border-l-2 border-gold-500/40"
              >
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  {row.question}
                </h3>
                <p className="text-slate-300 leading-relaxed mb-3">
                  {row.answer}
                </p>
                <div className="flex flex-wrap gap-3">
                  {row.slugs.map((slug) => {
                    const tool = toolBySlug(slug);
                    if (!tool) return null;
                    return (
                      <Link
                        key={slug}
                        href={tool.href}
                        className="text-sm text-gold-400 hover:underline inline-block py-3 -my-3"
                      >
                        {tool.title} →
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ============ The toolkit, grouped ============ */}
        <section id="toolkit" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-4">
            The toolkit, in the order you would use it
          </h2>
          <p className="text-slate-300 leading-relaxed max-w-3xl mb-10">
            Evaluating a junior moves through five stages: narrowing the field,
            valuing what is left, reading how it is financed, testing whether it
            is tradeable and genuinely active, and finally reading the technical
            documents. The tools are grouped the same way.
          </p>
          <ToolsGrid />
        </section>

        {/* ============ Methodology ============ */}
        <section id="methodology" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-4">
            How the numbers are calculated
          </h2>
          <p className="text-slate-300 leading-relaxed max-w-3xl mb-8">
            Published in full, including the assumptions. A screener that will
            not tell you its formula is asking for trust it has not earned, and
            these metrics carry real caveats worth knowing before you act on
            them.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Market cap per contained ounce
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                Market capitalisation divided by total contained gold ounces
                across a company&apos;s reported resource categories. It is
                commonly called EV/oz, but note the caveat:{" "}
                <strong className="text-gold-400">
                  we use market capitalisation, not true enterprise value
                </strong>
                {" — "}cash and debt are not netted out. For a junior holding a
                large treasury after a raise, that understates how cheap the
                ounces are.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                Only meaningful against comparables at a similar stage and
                jurisdiction. An inferred ounce is not a reserve ounce.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Price to NAV (P/NAV)
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                Market capitalisation divided by the after-tax NPV at a 5%
                discount rate, as reported in the company&apos;s own technical
                study. Below 1.0 means the market values the company at less
                than the study&apos;s modelled project value.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                The NPV is the company&apos;s figure, at its own metal price
                assumptions — not an independent estimate. Treat a low P/NAV as
                a question to investigate, not an answer.{" "}
                <Link
                  href="/guides/how-to-read-ni-43-101-report"
                  className="text-gold-400 hover:underline"
                >
                  How to read an NI 43-101 report
                </Link>
                .
              </p>
            </div>

            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Days to exit
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                We take the median daily dollar volume over the last 60 trading
                sessions, assume you can be{" "}
                <strong className="text-gold-400">
                  20% of a day&apos;s volume
                </strong>{" "}
                without moving the price — the conventional planning figure for
                thin listings — and divide your position size by the result.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                A 60-session median is long enough to survive a quiet fortnight
                but short enough to reflect a stock that has recently woken up.
                Listings are banded: under $1,000 a day is treated as
                untradeable, under $5,000 as very thin.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Signal-to-noise ratio
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                Every press release is classified by type. The ratio is the
                share reporting an actual result —{" "}
                <strong className="text-gold-400">
                  drill results, resource updates, or study results
                </strong>{" "}
                — against total releases over the window. Everything else counts
                as noise: grants, appointments, conference attendance.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                Companies with fewer than 10 releases are excluded, because the
                ratio is meaningless on a small sample.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Metal correlation, beta and R²
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                Computed on overlapping daily returns for the stock and the
                chosen metal. Correlation measures whether they move together;
                beta measures by how much. R² is the square of the correlation:
                the share of the stock&apos;s movement explained by the metal.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                A beta above 1 means the stock has historically amplified the
                metal&apos;s moves — in both directions. High beta with low R²
                means the amplification is unreliable.
              </p>
            </div>

            <div className="glass-card rounded-xl p-6">
              <h3 className="text-xl font-semibold text-slate-100 mb-3">
                Resource growth
              </h3>
              <p className="text-slate-300 leading-relaxed mb-3">
                Contained ounces, average grade and tonnage compared across
                successive NI 43-101 reports from the same company, so an
                increase driven by genuine drilling can be separated from one
                driven by reclassifying existing material or lowering the
                cut-off grade.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                See{" "}
                <Link
                  href="/guides/inferred-vs-indicated-vs-measured-resources"
                  className="text-gold-400 hover:underline"
                >
                  inferred vs indicated vs measured
                </Link>{" "}
                for why the category matters as much as the number.
              </p>
            </div>
          </div>
        </section>

        {/* ============ What the data says ============ */}
        {(illiquidPct || stats.signalPct) && (
          <section id="sector-findings" className="scroll-mt-20">
            <h2 className="text-3xl font-bold text-gold-400 mb-4">
              Two things the data says about junior mining
            </h2>
            <p className="text-slate-300 leading-relaxed max-w-3xl mb-8">
              Both of these come straight out of the tools above, recomputed
              against current data. Neither is visible on a conventional stock
              screener, and both should change how you size a position.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {illiquidPct !== null && (
                <div className="glass-card rounded-xl p-6">
                  <p className="text-5xl font-bold text-gold-400 mb-3 tabular-nums">
                    {illiquidPct}%
                  </p>
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">
                    of tracked companies are effectively untradeable
                  </h3>
                  <p className="text-slate-300 leading-relaxed">
                    {stats.illiquidCount} of {stats.liquidityUniverse} companies
                    have a median daily dollar volume under $5,000
                    {stats.medianDollarVolume
                      ? `, and the median across the whole universe is just $${stats.medianDollarVolume.toLocaleString()} a day`
                      : ""}
                    . At a 20% participation rate, a $25,000 position in a
                    typical listing takes weeks to unwind.
                  </p>
                  <Link
                    href="/investor-tools/liquidity-screener"
                    className="inline-flex items-center min-h-11 mt-4 text-sm text-gold-400 hover:underline"
                  >
                    Check any position size →
                  </Link>
                </div>
              )}

              {stats.signalPct !== null && (
                <div className="glass-card rounded-xl p-6">
                  <p className="text-5xl font-bold text-gold-400 mb-3 tabular-nums">
                    {stats.signalPct}%
                  </p>
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">
                    of junior mining news reports an actual result
                  </h3>
                  <p className="text-slate-300 leading-relaxed">
                    Across{" "}
                    {stats.totalReleases
                      ? `${stats.totalReleases.toLocaleString()} press releases`
                      : "every press release we track"}
                    , only about a quarter report drill results, a resource
                    update, or a study. The rest is corporate housekeeping —
                    which is exactly why release volume alone is a poor proxy
                    for activity.
                  </p>
                  <Link
                    href="/investor-tools/signal-to-noise"
                    className="inline-flex items-center min-h-11 mt-4 text-sm text-gold-400 hover:underline"
                  >
                    Compare any company →
                  </Link>
                </div>
              )}
            </div>
          </section>
        )}

        {/* ============ Worked example ============ */}
        <section id="worked-example" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-4">
            How to evaluate a junior in about ten minutes
          </h2>
          <p className="text-slate-300 leading-relaxed max-w-3xl mb-8">
            A repeatable order of operations. It is deliberately front-loaded
            with the checks most likely to disqualify a company, so you spend
            reading time only on names that survive.
          </p>

          <ol className="flex flex-col gap-5 max-w-3xl">
            {[
              {
                t: "Check you could get out before you look at anything else",
                d: "Run the position size you would actually take through Liquidity & Days to Exit. If the answer is weeks, nothing else on this list matters — size down or move on.",
                href: "/investor-tools/liquidity-screener",
              },
              {
                t: "Check the company is actually doing something",
                d: "Run the Signal-to-Noise Ratio. A company well below the sector norm is generating announcements without generating results.",
                href: "/investor-tools/signal-to-noise",
              },
              {
                t: "Read the capital structure before the geology",
                d: "Warrant Overhang Radar and Dilution Tracker. Find out how many shares already exist, how many more are coming, and at what price. A discovery you pay for twice is not a discovery.",
                href: "/investor-tools/warrant-radar",
              },
              {
                t: "Put a price on the ounces",
                d: "Peer Comparison for market cap per ounce and P/NAV against automatically detected comparables. You are looking for a gap you can explain, not just a low number.",
                href: "/investor-tools/peer-comparison",
              },
              {
                t: "Confirm the resource is growing for the right reason",
                d: "Resource Growth Tracker across successive technical reports. Rising ounces at falling grade often means a lower cut-off, not better drilling.",
                href: "/investor-tools/resource-growth",
              },
              {
                t: "Only now, read the technical report",
                d: "Ask the Due-Diligence Assistant your specific questions and get the exact NI 43-101 passages that answer them, with citations.",
                href: "/investor-tools/due-diligence",
              },
            ].map((step, i) => (
              <li key={step.t} className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-gold-500/15 border border-gold-500/30 text-gold-400 font-semibold flex items-center justify-center tabular-nums">
                  {i + 1}
                </span>
                <div>
                  <h3 className="text-lg font-semibold text-slate-100 mb-1">
                    {step.t}
                  </h3>
                  <p className="text-slate-300 leading-relaxed">
                    {step.d}{" "}
                    <Link
                      href={step.href}
                      className="text-gold-400 hover:underline whitespace-nowrap"
                    >
                      Open tool →
                    </Link>
                  </p>
                </div>
              </li>
            ))}
          </ol>

          <p className="text-slate-400 mt-8 max-w-3xl leading-relaxed">
            New to the sector? Start with{" "}
            <Link
              href="/guides/junior-gold-mining-companies-guide"
              className="text-gold-400 hover:underline"
            >
              our guide to junior gold mining companies
            </Link>{" "}
            and{" "}
            <Link
              href="/guides/how-junior-mining-companies-raise-money"
              className="text-gold-400 hover:underline"
            >
              how juniors raise money
            </Link>
            , or look up any unfamiliar term in the{" "}
            <Link href="/glossary" className="text-gold-400 hover:underline">
              mining glossary
            </Link>
            .
          </p>
        </section>

        {/* ============ FAQ ============ */}
        <section id="faq" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-8">
            Frequently asked questions
          </h2>
          <div className="flex flex-col gap-5 max-w-3xl">
            {FAQS.map((f) => (
              <div key={f.q} className="glass-card rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  {f.q}
                </h3>
                <p className="text-slate-300 leading-relaxed">{f.a}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ============ Related ============ */}
        <section id="related" className="scroll-mt-20">
          <h2 className="text-3xl font-bold text-gold-400 mb-6">
            Where to go next
          </h2>
          <div className="flex flex-wrap gap-3">
            {[
              { href: "/companies", label: "All companies" },
              { href: "/companies/commodity/gold", label: "Gold companies" },
              {
                href: "/companies/commodity/critical-minerals",
                label: "Critical minerals companies",
              },
              { href: "/open-financings", label: "Open financings" },
              {
                href: "/reports/financings",
                label: "Weekly financing roundup",
              },
              { href: "/glossary", label: "Mining glossary" },
              { href: "/guides", label: "Investment guides" },
              { href: "/metals", label: "Live metals prices" },
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="px-4 py-2.5 min-h-11 inline-flex items-center rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
              >
                {l.label} →
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
