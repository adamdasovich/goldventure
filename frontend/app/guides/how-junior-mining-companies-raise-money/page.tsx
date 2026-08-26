import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/SiteNav";
import { RelatedResources, OPEN_FINANCINGS, CLOSED_FINANCINGS } from "@/components/guides/RelatedResources";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/how-junior-mining-companies-raise-money";

export const metadata: Metadata = {
  title:
    "How Junior Mining Companies Raise Money: Placements, Flow-Through & Bought Deals",
  description:
    "How junior mining companies actually get funded. Private placements, bought deals, flow-through shares, warrants, ATM offerings, streams, and royalties — explained with worked dilution math.",
  keywords: [
    "how do junior mining companies raise money",
    "junior mining financing",
    "private placement mining",
    "bought deal financing",
    "flow-through shares Canada",
    "mining warrants explained",
    "CEE expenditure",
    "CDE expenditure",
    "at-the-market offering mining",
    "convertible debenture mining",
    "royalty stream financing",
  ],
  openGraph: {
    title: "How Junior Mining Companies Raise Money: A Complete Guide",
    description:
      "Private placements, bought deals, flow-through shares, warrants, ATMs, streams, and royalties — explained with the dilution math.",
    type: "article",
    url: CANONICAL,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "How Junior Mining Companies Raise Money",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "How Junior Mining Companies Raise Money",
    description:
      "Private placements, bought deals, flow-through, warrants, ATMs, streams, royalties — explained.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: CANONICAL,
  },
};

const articleSchema = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline:
    "How Junior Mining Companies Raise Money: Placements, Flow-Through & Bought Deals Explained",
  description:
    "A comprehensive guide to junior mining financing: private placements, bought deals, flow-through shares, warrants, ATMs, streams, and royalties, with worked dilution math.",
  author: {
    "@type": "Organization",
    name: "Junior Mining Intelligence",
    url: "https://juniorminingintelligence.com",
  },
  publisher: {
    "@type": "Organization",
    name: "Junior Mining Intelligence",
    logo: {
      "@type": "ImageObject",
      url: "https://juniorminingintelligence.com/logo.png",
    },
  },
  datePublished: "2026-05-28",
  dateModified: "2026-05-28",
  mainEntityOfPage: { "@type": "WebPage", "@id": CANONICAL },
  about: [
    { "@type": "Thing", name: "Mining Finance" },
    { "@type": "Thing", name: "Private Placement" },
    { "@type": "Thing", name: "Flow-Through Shares" },
  ],
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "How do junior mining companies raise money?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Junior mining companies fund themselves primarily through equity financings — selling new shares to investors. The most common instruments are private placements (selling shares to selected investors with hold periods), bought deals (underwriters buy the full offering and resell), flow-through shares (Canadian tax-advantaged shares for exploration spending), and at-the-market offerings (continuous sales on the market). Non-dilutive alternatives include royalty and stream agreements, convertible debentures, and project-level joint ventures. Pre-revenue exploration companies depend on these financings to fund drilling, technical studies, and overhead — typically raising every 12-24 months until production cash flow begins.",
      },
    },
    {
      "@type": "Question",
      name: "What is a private placement in mining?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A private placement is the sale of new shares (and sometimes warrants) to a specific group of investors outside a public offering. In Canada, private placements rely on prospectus exemptions — most commonly the Accredited Investor exemption, the Offering Memorandum exemption, or (for very small raises) the Family/Friends/Business Associates exemption. Private placements are faster and cheaper than public offerings: a junior can announce, price, and close a placement in 2-4 weeks. The trade-off for investors is a hold period (4 months in Canada under National Instrument 45-102) before the shares can be resold on the public market.",
      },
    },
    {
      "@type": "Question",
      name: "What is a bought deal?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A bought deal is an underwritten financing where the investment bank (or syndicate of banks) commits to purchase the entire offering at a fixed price, then resells the shares to investors. The company gets certainty: the cash arrives whether or not the bank successfully resells. The bank takes the inventory risk in exchange for a meaningful fee (typically 5-7% of proceeds for junior miners). Bought deals are the gold standard for established issuers — the announcement itself signals to the market that institutional underwriters have validated the issuer and the use of proceeds. Bought deals only work above a certain size threshold; placements under ~$10M rarely attract underwriter interest.",
      },
    },
    {
      "@type": "Question",
      name: "What are flow-through shares in Canada?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Flow-through shares are a uniquely Canadian instrument that lets mining and energy exploration companies pass through certain tax deductions to investors. Specifically, qualifying Canadian Exploration Expenses (CEE) are renounced by the company to the investor, who claims them as a personal tax deduction (worth ~40-50% of the cost depending on province and income). In exchange, the investor pays a premium over the company's regular share price — typically 25-40% — to compensate for the future capital gains tax payable when the shares are eventually sold (since the adjusted cost base is reset to zero). Flow-through shares only exist because Canada is one of the few jurisdictions with this tax structure, and they fund a meaningful share of all Canadian junior exploration activity.",
      },
    },
    {
      "@type": "Question",
      name: "What is the difference between a bought deal and a marketed deal?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A bought deal is firm-committed: the underwriter buys the entire offering up-front. A marketed deal is a best-efforts offering: the underwriter agrees to use 'commercially reasonable efforts' to sell the offering but bears no inventory risk. Marketed deals typically include a 1-3 day book-building window where the underwriter gauges investor demand before final pricing. The pricing discount on a marketed deal is usually wider than a bought deal because the bank is selling without commitment. From a market-signalling perspective, bought deals are stronger because they imply the underwriter is confident the offering will sell.",
      },
    },
    {
      "@type": "Question",
      name: "What are warrants in mining financings?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Warrants are options issued alongside shares in many junior mining placements. A typical 'unit' financing might consist of one common share plus one-half warrant at $0.60, exercisable at $0.85 for two years. The warrant gives the investor the right to buy another share at the strike price within the term. Warrants make the financing more attractive to investors but create future dilution: if the stock rises and warrants are exercised, the company issues more shares (more cash in, but more shares outstanding). Heavily-warranted juniors can have effective share counts 30-50% higher than what their basic share count suggests — always check fully-diluted share counts in financing announcements.",
      },
    },
    {
      "@type": "Question",
      name: "What is an at-the-market (ATM) offering?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "An at-the-market (ATM) offering is a continuous, dribble-out sale of new shares directly into the public market at prevailing prices. Instead of pricing one block of shares to a group of investors, the company files a shelf prospectus and then sells small daily quantities through an underwriter over weeks or months. ATMs are administratively efficient, avoid the discount typical of bulk financings, and let companies raise opportunistically when the share price is strong. They are more common for mid-tier producers than early-stage juniors because they require an existing shelf prospectus and meaningful average daily trading volume. The downside: ATM sales suppress the share price as supply hits the market continuously.",
      },
    },
    {
      "@type": "Question",
      name: "What is a stream or royalty deal?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Streams and royalties are non-dilutive financing structures. A royalty entitles the financier to a fixed percentage of future revenue or production from a specific project — often 1-3% of net smelter return (NSR). A stream entitles the financier to purchase a portion of future production at a fixed (below-market) price. Both deliver large upfront payments without issuing equity, but they encumber the project's future cash flow indefinitely. Companies like Franco-Nevada, Wheaton Precious Metals, and Royal Gold are the major dedicated buyers. Streams and royalties are increasingly common for mid-stage juniors funding mine construction, because the alternative (massive equity dilution at low share prices) is often worse for existing shareholders.",
      },
    },
    {
      "@type": "Question",
      name: "What is dilution and how do I calculate it?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Dilution is the reduction in your percentage ownership when a company issues new shares. The math is straightforward: if a company has 100 million shares outstanding and issues 20 million new shares, the share count rises 20% — your stake is now 20% diluted. The same dilution math applies to the warrant overhang: if the company has 100 million shares plus 30 million in-the-money warrants, your real ownership exposure is 100/130 = 77% of basic. The deeper question is value dilution: a financing that raises $5M for a $50M-market-cap company at the current share price doesn't destroy value per share — it raises the same value the dilution removes. A financing priced at a 30% discount, however, transfers value from existing shareholders to the new investors. Always check pricing vs. the share price the day before the announcement.",
      },
    },
    {
      "@type": "Question",
      name: "How often do junior miners raise money?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Pre-revenue junior exploration companies typically raise every 12-24 months, with raise size scaled to the next 12-18 months of planned spending. A common cadence is: raise $3-8M in private placement to fund a drill program (4-6 months of work), report results, raise again if results were positive. Companies advancing toward production raise larger amounts less frequently — for example, a single $50-200M financing to fund a feasibility study or construction. The 'cash runway' to the next financing is one of the most important diligence checks: a junior with 3 months of cash left will dilute on whatever terms it can get, which is usually unfavorable to existing shareholders.",
      },
    },
  ],
};

const howToSchema = {
  "@context": "https://schema.org",
  "@type": "HowTo",
  name: "How to Read a Junior Mining Financing Announcement",
  description: "Step-by-step workflow for assessing a junior mining financing.",
  totalTime: "PT5M",
  step: [
    {
      "@type": "HowToStep",
      name: "Identify the structure",
      text: "Private placement, bought deal, marketed deal, ATM, flow-through, or convertible debt — each has different signalling and dilution implications.",
    },
    {
      "@type": "HowToStep",
      name: "Calculate the discount to market",
      text: "Compare the issue price to the share price the day before announcement. Discounts under 10% are healthy; 20%+ discounts signal weak demand or distress.",
    },
    {
      "@type": "HowToStep",
      name: "Compute the dilution",
      text: "New shares ÷ current shares outstanding. Then add the warrant overhang at exercise. A 'small 10% raise' that comes with full warrant coverage can be a 20% fully-diluted dilution event.",
    },
    {
      "@type": "HowToStep",
      name: "Check use of proceeds",
      text: "Drill program, study, working capital, debt repayment — each has different value-creation potential. 'General corporate purposes' is the weakest disclosure.",
    },
    {
      "@type": "HowToStep",
      name: "Note the lead order and strategic participants",
      text: "Insider participation and named strategic investors (royalty companies, larger miners) is a positive signal. Anonymous retail-only books are weaker.",
    },
  ],
};

export default function FinancingPillarGuide() {
  return (
    <>
      <SiteNav />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />

      <div className="min-h-screen bg-slate-900">
        <div className="bg-gradient-to-b from-slate-800 to-slate-900 border-b border-slate-700">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <nav className="text-sm mb-6">
              <ol className="flex items-center space-x-2 text-slate-400">
                <li>
                  <Link href="/" className="hover:text-gold-400">
                    Home
                  </Link>
                </li>
                <li>/</li>
                <li>
                  <Link href="/guides" className="hover:text-gold-400">
                    Guides
                  </Link>
                </li>
                <li>/</li>
                <li className="text-slate-300">
                  How Junior Mining Companies Raise Money
                </li>
              </ol>
            </nav>

            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-slate-50 mb-6 tracking-tight">
              How Junior Mining Companies Raise Money
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              The complete guide to junior mining financing. Private placements,
              bought deals, flow-through shares, warrants, ATMs, streams, and
              royalties — with the dilution math worked out.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: May 28, 2026</span>
              <span>22 min read</span>
              <span>5,600 words</span>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 30-second answer */}
          <div className="bg-gradient-to-br from-gold-500/10 to-gold-500/5 border border-gold-500/30 rounded-lg p-6 mb-12">
            <h2 className="text-lg font-bold text-gold-400 mb-3">
              The 30-second answer
            </h2>
            <p className="text-slate-200 mb-3">
              Junior mining companies are almost always pre-revenue. They fund
              themselves by repeatedly selling new shares. The instruments fall
              into four families:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-slate-200">
              <li>
                <strong className="text-gold-400">Private placements</strong> —
                sold to specific investors, with hold periods. The workhorse.
              </li>
              <li>
                <strong className="text-gold-400">
                  Bought deals & marketed deals
                </strong>{" "}
                — sold through underwriters into a wider pool. Larger raises.
              </li>
              <li>
                <strong className="text-gold-400">Flow-through shares</strong> —
                Canadian-specific, tax-advantaged for exploration spending.
                Premium-priced.
              </li>
              <li>
                <strong className="text-gold-400">
                  Non-dilutive: streams, royalties, debt
                </strong>{" "}
                — sell future cash flow instead of equity. Common at later
                stages.
              </li>
            </ul>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              The cadence is typically every 12–24 months for early-stage
              juniors. The terms — discount to market, warrant coverage,
              participating investors — tell you more about the company than the
              raise size does.
            </p>
          </div>

          {/* TOC */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-12">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Table of Contents
            </h2>
            <ol className="space-y-2 text-slate-300 list-decimal pl-6">
              <li>
                <a href="#lifecycle" className="hover:text-gold-400">
                  The funding lifecycle of a junior miner
                </a>
              </li>
              <li>
                <a href="#private-placements" className="hover:text-gold-400">
                  Private placements — the workhorse
                </a>
              </li>
              <li>
                <a href="#bought-vs-marketed" className="hover:text-gold-400">
                  Bought deals vs marketed deals
                </a>
              </li>
              <li>
                <a href="#flow-through" className="hover:text-gold-400">
                  Flow-through shares — the Canadian advantage
                </a>
              </li>
              <li>
                <a href="#warrants-units" className="hover:text-gold-400">
                  Warrants and unit financings
                </a>
              </li>
              <li>
                <a href="#atm" className="hover:text-gold-400">
                  At-the-market (ATM) offerings
                </a>
              </li>
              <li>
                <a href="#cpc-rto" className="hover:text-gold-400">
                  CPCs and reverse takeovers
                </a>
              </li>
              <li>
                <a href="#streams-royalties" className="hover:text-gold-400">
                  Streams, royalties, and convertible debentures
                </a>
              </li>
              <li>
                <a href="#dilution-math" className="hover:text-gold-400">
                  Dilution math — a worked example
                </a>
              </li>
              <li>
                <a href="#reading-announcement" className="hover:text-gold-400">
                  How to read a financing announcement
                </a>
              </li>
              <li>
                <a href="#red-flags" className="hover:text-gold-400">
                  10 red flags
                </a>
              </li>
              <li>
                <a href="#tools" className="hover:text-gold-400">
                  Tools to speed this up
                </a>
              </li>
              <li>
                <a href="#faq" className="hover:text-gold-400">
                  FAQ
                </a>
              </li>
            </ol>
          </div>

          <article className="prose prose-invert prose-slate max-w-none">
            {/* Section 1 — Lifecycle */}
            <section id="lifecycle" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The funding lifecycle of a junior miner
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A typical junior mining company moves through six funding phases
                over its life. Knowing which phase a company is in tells you
                what kind of financing to expect — and what to worry about.
              </p>
              <div className="space-y-4 mb-6">
                {[
                  {
                    phase: "1. Seed",
                    raise: "$50K – $500K",
                    desc: "Founders, family-and-friends, angel investors. Used to stake claims, commission initial geology work, and prepare for an IPO. Often structured as common shares at $0.05–$0.15.",
                  },
                  {
                    phase: "2. IPO / CPC",
                    raise: "$1M – $5M",
                    desc: "Public listing via traditional IPO or via Capital Pool Company (CPC) qualifying transaction. First broad investor base. Issue price typically $0.20–$0.30. Lock-up periods for insiders.",
                  },
                  {
                    phase: "3. Early exploration",
                    raise: "$3M – $10M per round",
                    desc: "Private placements to fund first systematic drill programmes. Often combined with flow-through shares. Cadence: every 12–18 months until discovery or capitulation.",
                  },
                  {
                    phase: "4. Resource definition",
                    raise: "$10M – $30M per round",
                    desc: "Larger placements or bought deals to fund infill drilling, metallurgy, and PEAs. Strategic investors and major mining companies start participating. Warrant coverage shrinks.",
                  },
                  {
                    phase: "5. Feasibility & permitting",
                    raise: "$30M – $100M+",
                    desc: "Bought deals, ATMs, and structured equity. PFS and DFS spending is real money. Early streams or royalties may appear here for projects with clear economics.",
                  },
                  {
                    phase: "6. Construction & production",
                    raise: "$100M – $1B+",
                    desc: "Project finance debt, streams, royalties, and equity. Construction lenders require DFS-grade reserves. Largest single dilution events occur here, often via concurrent debt + equity packages.",
                  },
                ].map((p, i) => (
                  <div
                    key={i}
                    className="bg-slate-800/50 border-l-4 border-gold-500/60 rounded-r-lg p-4"
                  >
                    <div className="flex flex-wrap items-baseline gap-x-3 mb-1">
                      <h3 className="text-lg font-bold text-gold-400">
                        {p.phase}
                      </h3>
                      <span className="text-sm text-slate-400 font-mono">
                        {p.raise}
                      </span>
                    </div>
                    <p className="text-slate-300 text-sm mb-0">{p.desc}</p>
                  </div>
                ))}
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The vast majority of TSXV-listed juniors live in phases 3 and 4
                — perpetually raising, drilling, and re-raising. Few reach
                production. The financing cadence is the heartbeat of the
                business model.
              </p>
            </section>

            {/* Section 2 — Private Placements */}
            <section id="private-placements" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Private placements — the workhorse
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A <strong className="text-gold-400">private placement</strong>{" "}
                is the sale of new shares (and often warrants) to a specific
                group of investors outside a public market offering. It is by
                far the most common financing structure for early- and mid-stage
                juniors, accounting for the majority of dollars raised on the
                TSXV in any given year.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                How it works
              </h3>
              <ol className="list-decimal pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  The company decides on a raise size and price, often after
                  informal soundings with brokers, insiders, or existing
                  shareholders.
                </li>
                <li>
                  A press release announces the offering: total size, issue
                  price, structure (units vs. straight common), warrant terms if
                  applicable, and use of proceeds.
                </li>
                <li>
                  Investors subscribe through subscription agreements citing a
                  specific prospectus exemption (most commonly Accredited
                  Investor, Offering Memorandum, or Family/Friends/Business
                  Associates).
                </li>
                <li>
                  Funds are deposited in trust. The placement closes when
                  conditions are met (regulatory approvals, minimum
                  subscription).
                </li>
                <li>
                  Investors receive certificates with a legend restricting
                  resale during the hold period — four months in Canada under
                  National Instrument 45-102.
                </li>
              </ol>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Why it dominates
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Speed.</strong> Two to four
                  weeks from announcement to close, vs. months for a prospectus
                  offering.
                </li>
                <li>
                  <strong className="text-gold-400">Low cost.</strong> No
                  prospectus drafting, no auditor reviews of new financial
                  disclosures, no exchange filing fees beyond the basic
                  treasury-share-issuance fee.
                </li>
                <li>
                  <strong className="text-gold-400">Flexibility.</strong>{" "}
                  Companies can structure unit financings, multiple tranches,
                  flow-through and non-flow-through portions concurrently.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Targeted investor base.
                  </strong>{" "}
                  Companies can pre-place with strategic investors (royalty
                  funds, larger miners) before opening to retail.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                For a focused deep-dive on private placement mechanics,
                exemptions, and the subscription agreement process, see our{" "}
                <Link
                  href="/guides/how-junior-mining-companies-raise-money"
                  className="text-gold-400 hover:underline"
                >
                  Private Placements Guide
                </Link>
                .
              </p>
            </section>

            {/* Section 3 — Bought vs Marketed */}
            <section id="bought-vs-marketed" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Bought deals vs marketed deals
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                When a junior gets large enough — typically above ~$10M of
                planned raise — investment banks become involved as
                underwriters. There are three primary structures:
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Structure
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Underwriter risk
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Typical discount
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Speed
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Signal
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Bought deal
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Bank commits firm capital
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        5–10%
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Fast (overnight pricing)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-emerald-300">
                        Strong
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Marketed deal
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Best efforts
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        10–20%
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1–3 day book-build
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-yellow-300">
                        Moderate
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Best-efforts
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Best efforts, no commitment
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        15–30%
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Variable
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-red-300">
                        Weak
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The bought deal is the gold standard. The bank, by committing
                its own capital, is implicitly endorsing the issuer. The
                announcement effect is positive even before the resale completes
                because institutional underwriters do not commit without high
                confidence that the offering will clear.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A marketed deal — or worse, a pure best-efforts placement at a
                steep discount — signals weaker institutional demand. The wider
                discount compensates buyers for the perceived risk. Repeated
                best-efforts deals from the same issuer at growing discounts are
                a classic distress pattern.
              </p>
            </section>

            {/* Section 4 — Flow-through */}
            <section id="flow-through" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Flow-through shares — the Canadian advantage
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                <strong className="text-gold-400">Flow-through shares</strong>{" "}
                are a uniquely Canadian instrument that lets mining and energy
                companies pass through certain tax deductions to investors. They
                exist because the Canadian government wants to encourage
                domestic exploration, and they fund a meaningful share of all
                Canadian junior mining activity.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                The mechanics
              </h3>
              <ol className="list-decimal pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  The company issues flow-through shares at a premium to the
                  market price — typically 25–40% above.
                </li>
                <li>
                  The cash raised must be spent on{" "}
                  <strong className="text-gold-400">
                    Canadian Exploration Expenses (CEE)
                  </strong>{" "}
                  — qualifying exploration work in Canada, primarily drilling
                  and geological work prior to discovery.
                </li>
                <li>
                  The company renounces the right to deduct those expenses
                  itself. Instead, the investor takes the deduction on their
                  personal tax return, typically worth 40–50% of the share price
                  depending on income bracket and province.
                </li>
                <li>
                  The investor&apos;s adjusted cost base in the shares becomes
                  zero — when they eventually sell, the entire sale price is a
                  capital gain.
                </li>
              </ol>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Worked example
              </h3>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 mb-4">
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Common share price: $0.40
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Flow-through price: $0.55 (38% premium)
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Investor in 45% tax bracket pays $0.55 per share
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Tax deduction worth: 0.55 × 45% = $0.247
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Net cost after deduction: $0.303 per share
                </p>
                <p className="text-slate-300 mb-0 font-mono text-sm font-bold text-gold-400">
                  Effective discount to market: $0.40 − $0.303 = $0.097 (24%
                  below market)
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A high-income Canadian investor can effectively buy mining
                shares at a 20–25% discount to the public market, with the catch
                being that they lose the cost basis and pay full capital gains
                on resale. For the company, the advantage is even bigger: they
                raise capital at a 30%+ premium to the regular share price.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Charity flow-through (a sub-variant worth knowing)
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                In a charity flow-through structure, the investor buys
                flow-through shares, immediately donates them to a registered
                charity for a charitable tax receipt at fair market value, and
                the charity sells the shares to a liquidity provider at a
                pre-arranged price. The investor captures both the flow-through
                deduction AND a charitable donation receipt — effectively buying
                mining exposure at deep negative net cost. Charity flow-through
                deals routinely close at 70–90% premiums to the underlying share
                price.
              </p>
              {/* The companion deep-dive is not written yet. Do NOT link it
                  until /guides/flow-through-shares-explained exists — a live
                  <Link> to a missing route is a hard 404 to Googlebot, which
                  reads none of the "(coming soon)" reassurance a human does.
                  This one showed up in Search Console's Not-found report. */}
              <p className="text-slate-300 mb-4 leading-relaxed">
                Flow-through is one of the most under-explained financing
                instruments online. A dedicated deep-dive covering CEE vs CDE,
                the look-back rule, super flow-through, and province-by-province
                credit calculations is in the works.
              </p>
            </section>

            {/* Section 5 — Warrants */}
            <section id="warrants-units" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Warrants and unit financings
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A <strong className="text-gold-400">warrant</strong> is an
                option attached to a share, giving the holder the right to buy
                another share at a fixed price within a specified time. A{" "}
                <strong className="text-gold-400">unit financing</strong>{" "}
                bundles one share with some number of warrants (commonly 1/2 or
                1 full warrant per share).
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Reading a typical unit financing announcement: &quot;100 million
                units at $0.50, each unit consisting of one common share and
                one-half common share purchase warrant. Each whole warrant
                entitles the holder to purchase one additional common share at
                $0.75 for 24 months.&quot;
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">Decoded:</p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Now:</strong> 100M new
                  shares issued for $50M cash.
                </li>
                <li>
                  <strong className="text-gold-400">Future overhang:</strong>{" "}
                  50M warrants (one-half × 100M units). If the stock trades
                  above $0.75 over 24 months, these will likely be exercised —
                  issuing 50M more shares for $37.5M more cash.
                </li>
                <li>
                  <strong className="text-gold-400">Fully diluted:</strong> the
                  financing represents up to 150M new shares — 50% more dilution
                  than the headline 100M.
                </li>
              </ul>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Warrant coverage as a market signal
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    1/4 warrant per share or none:
                  </strong>{" "}
                  signals strong demand. The company didn&apos;t need to sweeten
                  the deal.
                </li>
                <li>
                  <strong className="text-gold-400">
                    1/2 warrant per share:
                  </strong>{" "}
                  standard for healthy junior placements.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Full warrant per share:
                  </strong>{" "}
                  meaningful sweetener. Often seen when stock is weak or
                  exploration is mid-program.
                </li>
                <li>
                  <strong className="text-gold-400">
                    2 warrants per share + finder warrants + extended term:
                  </strong>{" "}
                  signal of weak demand. Distress pricing.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The warrant strike price matters too. Warrants struck at the
                financing price (or below) are deeply in-the-money and
                effectively free shares. Warrants struck at meaningful premiums
                signal that the company expects upside and doesn&apos;t want to
                give away too much.
              </p>
            </section>

            {/* Section 6 — ATM */}
            <section id="atm" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                At-the-market (ATM) offerings
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                An <strong className="text-gold-400">ATM offering</strong> lets
                a company sell new shares directly into the public market over
                time, at prevailing prices, rather than in a discrete block at a
                discount.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Mechanics: the company files a base shelf prospectus (good for
                25 months) and enters into an ATM equity distribution agreement
                with an underwriter. The company can then instruct the
                underwriter to sell up to X shares or up to $Y in any given
                period. The shares trade through the public market as ordinary
                volume.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">Advantages:</p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  No discount to market — shares sell at prevailing prices.
                </li>
                <li>
                  Opportunistic — companies can pause sales when the price is
                  weak and accelerate when strong.
                </li>
                <li>
                  Administratively cheap — once the shelf is filed, ongoing
                  sales are routine.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Disadvantages:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  Continuous supply suppresses price — the share price often
                  drifts lower during active ATM periods.
                </li>
                <li>
                  Requires existing meaningful average daily trading volume —
                  small-cap juniors with $50K average daily volume cannot ATM
                  raise $20M without crushing the stock.
                </li>
                <li>
                  Disclosure is typically retrospective (quarterly) — you may
                  not know an ATM is active until after the fact.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                ATMs are far more common for mid-tier producers and developers
                than for early-stage juniors. If you see an early-stage junior
                with an active ATM, expect downward share-price pressure for as
                long as the program is running.
              </p>
            </section>

            {/* Section 7 — CPC/RTO */}
            <section id="cpc-rto" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                CPCs and reverse takeovers
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Not all juniors go public via traditional IPO. Two alternative
                paths dominate the TSXV.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Capital Pool Companies (CPCs)
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A CPC is a shell company listed on the TSXV with no assets other
                than cash. CPCs raise $200K to $500K from public investors, then
                have 24 months to complete a{" "}
                <strong className="text-gold-400">
                  Qualifying Transaction (QT)
                </strong>{" "}
                — typically the acquisition of a private mining company. Once
                the QT closes, the CPC becomes a regular TSXV-listed miner with
                the former CPC investors as shareholders. CPCs are the cheapest,
                fastest path to a TSXV listing — they effectively recycle the
                listing of a shell with a private exploration company looking to
                go public.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Reverse Takeovers (RTOs)
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                An RTO is essentially the same idea but at larger scale and
                without the CPC formalities. A private mining company acquires
                (and is reverse-acquired by) a dormant listed company. The
                result is identical: a private company gets a public listing
                without going through a full IPO. RTOs are common when a former
                producer or failed explorer with a listing but no operations
                gets acquired by a new private project.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                For investors, CPC and RTO listings should be treated with extra
                scrutiny. The private company being injected hasn&apos;t been
                through public-company disclosure for a sustained period. Look
                hard at the qualifying valuation, the working capital position,
                and the new management team.
              </p>
            </section>

            {/* Section 8 — Streams/Royalties */}
            <section id="streams-royalties" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Streams, royalties, and convertible debentures
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                These are the main non-dilutive (or partially non-dilutive)
                financing instruments. They are most common in phases 5–6 of the
                lifecycle, when a project is advancing toward construction and
                equity dilution is least attractive.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Royalties
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A royalty entitles the holder to a fixed percentage of future
                project revenue or production. The most common form is a{" "}
                <strong className="text-gold-400">
                  Net Smelter Return (NSR)
                </strong>{" "}
                royalty — typically 1–3% of gross revenue net of refining and
                transport costs. The company gets a large upfront cash payment
                (often $10M–$100M); the royalty holder gets a perpetual share of
                future revenue.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Royalties are off-balance-sheet, don&apos;t dilute equity, and
                survive any future equity changes. They&apos;re also expensive
                in present-value terms — a 2% NSR on a 10-year mine could
                ultimately deliver 5–10x the upfront amount paid. Royalty
                companies (Franco-Nevada, Royal Gold, Wheaton, Triple Flag) run
                multi-billion-dollar businesses entirely on this model.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Streams
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A stream entitles the holder to purchase a fixed percentage of
                future production at a fixed, well-below-market price (often
                $400–$500/oz Au for gold streams). The mining company gets the
                upfront cash and a guaranteed buyer; the stream holder captures
                the margin between the fixed purchase price and the spot price.
                Streams are common for by-product metals — for example, a copper
                mine selling its silver and gold by-product as a stream funds a
                portion of construction without giving up the primary copper
                revenue.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Convertible debentures
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A convertible debenture is debt that can be converted into
                shares at a fixed conversion price. The company gets the cash
                without immediate dilution and pays interest (typically 6–10%
                for junior miners). If the share price rises above the
                conversion price, the debenture holder converts to equity. If it
                doesn&apos;t, the debenture is repaid at maturity (usually 2–5
                years).
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Convertible debentures are middle ground: less dilutive upfront
                than equity, less encumbering long-term than royalties or
                streams. The risk is the company can&apos;t repay at maturity if
                shares haven&apos;t converted — in which case the debenture
                either restructures, the company does an emergency equity raise,
                or both.
              </p>
            </section>

            {/* Section 9 — Dilution Math */}
            <section id="dilution-math" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Dilution math — a worked example
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Consider a junior explorer with the following profile, the day
                before announcing a financing:
              </p>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 mb-4">
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Shares outstanding (basic): 80,000,000
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Existing warrants outstanding: 12,000,000 @ $0.45 strike
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Existing options: 6,000,000 @ avg $0.30 strike
                </p>
                <p className="text-slate-300 mb-2 font-mono text-sm">
                  Share price (day before): $0.40
                </p>
                <p className="text-slate-300 mb-0 font-mono text-sm font-bold text-gold-400">
                  Basic market cap: $32M | Fully-diluted: ~$39M
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The company announces a $6M unit financing at $0.35 per unit,
                each unit consisting of one share and one-half warrant
                exercisable at $0.50 for 24 months. Let&apos;s compute the
                dilution and the discount.
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Step
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Calculation
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Result
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        New units issued
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        $6,000,000 ÷ $0.35
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        17.14M units
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        New shares (immediate)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        17.14M units × 1 share
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        17.14M shares
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        New warrants issued
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        17.14M × 0.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        8.57M warrants
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        Discount to market
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        ($0.40 − $0.35) ÷ $0.40
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-yellow-300">
                        12.5%
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        Immediate dilution (basic)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        17.14M ÷ (80M + 17.14M)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-yellow-300">
                        17.6%
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        New fully-diluted share count
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        80M + 12M + 6M + 17.14M + 8.57M
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        123.71M
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        Cumulative warrant + option overhang
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-xs">
                        (12M + 6M + 8.57M) ÷ 97.14M basic
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-mono text-red-300">
                        27.4%
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Reading the table:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong>12.5% discount</strong> is on the high side of
                  healthy. Below 10% would signal strong demand; 15%+ starts to
                  look like distress.
                </li>
                <li>
                  <strong>17.6% immediate dilution</strong> is sizeable. The
                  raise is 19% of pre-deal market cap — not catastrophic but
                  meaningful.
                </li>
                <li>
                  <strong>27.4% cumulative overhang</strong> is the number that
                  matters longer-term. More than a quarter of the future
                  fully-diluted share count is sitting in warrants and options
                  waiting to be exercised. A meaningful share-price recovery
                  will trigger meaningful additional dilution before existing
                  shareholders capture the upside.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The same financing announcement could be read as &quot;company
                raises $6M to fund drill program&quot; or as &quot;company
                dilutes 17.6% at a 12.5% discount with another 27.4% overhang
                pending.&quot; Both are true. The second framing tells you more
                about your investment position.
              </p>
            </section>

            {/* Section 10 — Reading announcements */}
            <section id="reading-announcement" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                How to read a financing announcement
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A 5-minute checklist for any financing press release:
              </p>
              <ol className="list-decimal pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Structure.</strong> Private
                  placement? Bought deal? Marketed? ATM? Flow-through? Each has
                  different signalling.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Issue price vs. market.
                  </strong>{" "}
                  Compare to share price the trading day before announcement.
                  Under 10% discount = healthy; 20%+ = concerning.
                </li>
                <li>
                  <strong className="text-gold-400">Warrant coverage.</strong>{" "}
                  Half warrant = standard; full warrant = sweetened; two-warrant
                  or finder warrants = distress.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Size relative to market cap.
                  </strong>{" "}
                  A 10% raise is routine; a 30%+ raise is a major dilution
                  event.
                </li>
                <li>
                  <strong className="text-gold-400">Use of proceeds.</strong>{" "}
                  Drill program with specifics &gt; resource update spending
                  &gt; working capital &gt; &quot;general corporate
                  purposes.&quot;
                </li>
                <li>
                  <strong className="text-gold-400">
                    Insider participation.
                  </strong>{" "}
                  Insiders taking up part of the placement = positive. Insiders
                  selling existing shares concurrently = negative.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Strategic participants.
                  </strong>{" "}
                  Named royalty funds, major miners, or institutional names
                  signal external validation. &quot;Sold to a group of
                  accredited investors&quot; with no names usually means
                  retail-broker channels.
                </li>
                <li>
                  <strong className="text-gold-400">Pricing context.</strong> Is
                  the share price at a 52-week high or low? Companies prefer to
                  raise on strength; raises into weakness signal that the
                  company couldn&apos;t wait.
                </li>
              </ol>
            </section>

            {/* Section 11 — Red flags */}
            <section id="red-flags" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                10 financing red flags
              </h2>
              {[
                {
                  n: 1,
                  title: "Best-efforts placement at 20%+ discount",
                  body: "The company couldn't get a bought deal commitment and is selling at a steep discount to attract buyers. Almost always signals weak institutional demand.",
                },
                {
                  n: 2,
                  title: "Repeated raises at progressively lower prices",
                  body: "A company that raised at $0.60 a year ago, $0.40 six months ago, and $0.25 now is in a downtrend the market has noticed. Each new raise sets the new ceiling.",
                },
                {
                  n: 3,
                  title: "Full warrants + finder warrants + extended term",
                  body: "When the warrant coverage gets generous, it's because the cash wasn't easy to find. Finder warrants (paid to brokers) are also dilutive and rarely highlighted.",
                },
                {
                  n: 4,
                  title: "Cash runway under 6 months",
                  body: "A junior with 3-4 months of cash left has lost pricing power. The next financing will be done on whatever terms the market gives, which is rarely favourable.",
                },
                {
                  n: 5,
                  title: "Use of proceeds is 'general corporate purposes'",
                  body: "Specific exploration programs create value. 'GCP' usually means overhead, salaries, and unspecified spending — the weakest dollar.",
                },
                {
                  n: 6,
                  title: "Insider selling alongside the raise",
                  body: "Insiders should be net buyers when they want capital for the business. Insider selling concurrent with a financing signals they think the price is high enough to step away.",
                },
                {
                  n: 7,
                  title: "Financing immediately before a known catalyst",
                  body: "Raising at $0.50 the day before drill assays drop suggests the company knows the assays will be disappointing. Conversely, raising at $0.50 after assays come in strong suggests the company is using strength to capitalise.",
                },
                {
                  n: 8,
                  title: "Recurring ATM activity with no announcement",
                  body: "ATMs are often disclosed only in quarterly filings. A company quietly running an ATM into a weak stock is suppressing price without telling you.",
                },
                {
                  n: 9,
                  title: "Convertible debenture with low conversion price",
                  body: "A convertible struck at or below the current share price will almost certainly convert — it's equity with extra steps. The interest cost was just wasted optics.",
                },
                {
                  n: 10,
                  title: "Stream or royalty taken at high effective cost",
                  body: "Royalties and streams are non-dilutive but expensive. A 2% NSR sold to fund a drill program in a phase-3 junior is selling future cash flow for very short-term needs. Streams at unfavourable prices can encumber a project for its entire mine life.",
                },
              ].map((flag) => (
                <div
                  key={flag.n}
                  className="mb-5 bg-slate-800/50 border border-slate-700 rounded-lg p-5"
                >
                  <h4 className="text-lg font-bold text-red-300 mb-2">
                    {flag.n}. {flag.title}
                  </h4>
                  <p className="text-slate-300 mb-0 text-sm leading-relaxed">
                    {flag.body}
                  </p>
                </div>
              ))}
            </section>

            {/* Tools */}
            <section id="tools" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Tools to speed this up
              </h2>
              <div className="grid md:grid-cols-2 gap-4 my-6">
                <Link
                  href="/closed-financings"
                  className="block bg-slate-800 border border-gold-500/40 hover:border-gold-500 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Closed Financings Tracker →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Browse private placements, bought deals, and flow-through
                    raises across 390+ junior miners. Filter by structure, size,
                    discount, warrant coverage.
                  </p>
                </Link>
                <Link
                  href="/open-financings"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Open Financings →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Active and recently announced financings you might
                    participate in. Tiered access by accreditation level.
                  </p>
                </Link>
                <Link
                  href="/investor-tools/financing-flow"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Financing Flow Tracker →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Visualise capital flowing into the sector by structure,
                    metal, and exchange. See where institutional money is going.
                  </p>
                </Link>
                <Link
                  href="/guides/how-junior-mining-companies-raise-money"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Private Placements Guide →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Deep dive on placement mechanics, prospectus exemptions, and
                    the subscription agreement process.
                  </p>
                </Link>
              </div>
            </section>

            {/* FAQ */}
            <section id="faq" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Frequently Asked Questions
              </h2>
              {faqSchema.mainEntity.map((qa, i) => (
                <div
                  key={i}
                  className="mb-5 border-b border-slate-700/50 pb-5 last:border-b-0"
                >
                  <h3 className="text-xl font-semibold text-slate-200 mb-2">
                    {qa.name}
                  </h3>
                  <p className="text-slate-300 mb-0 leading-relaxed">
                    {qa.acceptedAnswer.text}
                  </p>
                </div>
              ))}
            </section>

            {/* Related */}
            <section className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Related guides
              </h2>
              <ul className="space-y-3">
                <li>
                  <Link
                    href="/guides/private-placements-and-warrants"
                    className="text-gold-400 hover:underline"
                  >
                    Private Placements &amp; Warrants Explained (Units, Strike,
                    Expiry) →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/guides/how-to-read-ni-43-101-report"
                    className="text-gold-400 hover:underline"
                  >
                    How to Read an NI 43-101 Report →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/guides/how-to-interpret-mining-drill-results"
                    className="text-gold-400 hover:underline"
                  >
                    How to Read Mining Drill Results →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/guides/junior-gold-mining-companies-guide"
                    className="text-gold-400 hover:underline"
                  >
                    The Complete Guide to Junior Gold Mining Companies →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/guides/how-junior-mining-companies-raise-money"
                    className="text-gold-400 hover:underline"
                  >
                    Private Placements Guide (Financial Hub) →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/glossary"
                    className="text-gold-400 hover:underline"
                  >
                    Mining Glossary →
                  </Link>
                </li>
              </ul>
            </section>
          
            <RelatedResources
              slugs={["financing-flow","dilution-tracker","warrant-radar"]} extra={[OPEN_FINANCINGS, CLOSED_FINANCINGS]}
              intro="Financings are only useful information while they are still open. These track the raises and what they cost existing holders:"
            />
          </article>
        </div>
      </div>
    </>
  );
}
