import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/SiteNav";
import { RelatedResources, OPEN_FINANCINGS, CLOSED_FINANCINGS } from "@/components/guides/RelatedResources";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/private-placements-and-warrants";

export const metadata: Metadata = {
  title: "Warrants and Units in Junior Mining Financings, Explained",
  description:
    "How junior mining private placements are structured — what a 'unit' is (share + warrant), how warrants work (strike price, expiry, half vs full warrants), how to read a private placement announcement, and where to find recent warrant financings.",
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: "Warrants and Units in Junior Mining Financings",
    description:
      "What a private placement unit is, how warrants work (strike, expiry, half vs full), how to read the announcement, and where to track recent junior mining warrant financings.",
    type: "article",
    url: CANONICAL,
    siteName: "Junior Mining Intelligence",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Junior Mining Private Placements & Warrants",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Warrants and Units in Junior Mining Financings",
    description:
      "Units = shares + warrants. How the structure works, how to read an announcement, and where to find recent junior mining warrant financings.",
    images: ["/og-image.png"],
  },
};

const articleSchema = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline: "Warrants and Units in Junior Mining Financings, Explained",
  description:
    "How junior mining private placements are structured as units of shares plus warrants, how warrants work, and how to read a private placement announcement.",
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
  datePublished: "2026-08-10",
  dateModified: "2026-08-10",
  mainEntityOfPage: { "@type": "WebPage", "@id": CANONICAL },
  about: [
    { "@type": "Thing", name: "Private Placement" },
    { "@type": "Thing", name: "Warrant (finance)" },
    { "@type": "Thing", name: "Junior Mining Financing" },
  ],
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is a unit in a junior mining private placement?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A unit is a bundled security sold in a private placement. Almost every junior mining unit is one common share plus a warrant (or a fraction of a warrant). Investors buy units at a set price — for example '$0.10 per unit, each unit comprising one common share and one-half of one common share purchase warrant.' The share gives immediate ownership; the warrant gives the right to buy more shares later at a fixed price.",
      },
    },
    {
      "@type": "Question",
      name: "How does a warrant work in a mining financing?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A warrant is the right — not the obligation — to buy one additional common share at a fixed exercise (strike) price before an expiry date, typically 12 to 36 months out. If the stock trades above the exercise price before expiry, the warrant is 'in the money' and the holder can exercise it for a profit, giving the company more cash. If the stock stays below the exercise price, the warrant expires worthless. Warrants are a sweetener that makes the placement more attractive without lowering the headline unit price.",
      },
    },
    {
      "@type": "Question",
      name: "What is the difference between a full warrant and a half warrant?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A full warrant means each unit includes one whole warrant, so one warrant buys one share. A half warrant (or 'one-half of one warrant') means each unit includes 0.5 of a warrant, so two units' worth of warrants are needed to buy a single share. Half-warrant deals dilute less and are common in stronger markets; full-warrant deals are a bigger sweetener used when a company needs to attract capital in a weak market.",
      },
    },
    {
      "@type": "Question",
      name: "What does 'each whole warrant exercisable at $0.15 for 24 months' mean?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "It means the exercise (strike) price of each whole warrant is $0.15, and the warrant can be exercised any time up to 24 months from the closing date. If the share trades above $0.15 during that window, exercising for $0.15 and selling at the market price is profitable, and the company collects $0.15 per share in new capital. After 24 months the warrant expires.",
      },
    },
    {
      "@type": "Question",
      name: "Do private placement warrants dilute existing shareholders?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Yes. The unit shares dilute immediately, and the warrants represent potential future dilution — if exercised, they add more shares to the count. A large warrant overhang can also cap the share price, because holders often sell into strength to lock in the spread between the market price and the exercise price. Reading the full unit terms (warrant coverage, exercise price, expiry) tells you how much future dilution is embedded in a financing.",
      },
    },
    {
      "@type": "Question",
      name: "What is an accelerated expiry or acceleration clause on a warrant?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "An acceleration clause lets the company force early exercise if the share price trades at or above a stated level (say $0.30) for a set number of consecutive days (often 10 or 20). When triggered, the company issues a notice and the warrants expire in ~30 days unless exercised. Acceleration clauses let a company pull in warrant capital sooner and clean up the warrant overhang when the stock is performing.",
      },
    },
    {
      "@type": "Question",
      name: "Where can I find recent junior mining private placements with warrants?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Junior Mining Intelligence tracks open (live) private placements and closed financings, including their unit structure and warrant terms, and publishes a weekly financing roundup of the raises announced each week across gold, silver, copper, lithium and critical minerals. See the open financings and weekly financing roundup pages for the latest warrant deals.",
      },
    },
  ],
};

export default function PrivatePlacementsWarrantsGuide() {
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
                  Private Placements &amp; Warrants
                </li>
              </ol>
            </nav>

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              Junior Mining Private Placements, Units &amp; Warrants
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              How junior mining raises are structured: what a &quot;unit&quot;
              is, how the warrant attached to it works, and how to read a
              private placement announcement line by line.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: August 10, 2026</span>
              <span>10 min read</span>
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
              Most junior mining private placements are sold in{" "}
              <strong className="text-gold-400">units</strong>. A unit is almost
              always{" "}
              <strong className="text-gold-400">
                one common share plus a warrant
              </strong>{" "}
              (or half a warrant).
            </p>
            <ul className="list-disc pl-6 space-y-1 text-slate-200">
              <li>
                The <strong>share</strong> gives you immediate ownership.
              </li>
              <li>
                The <strong>warrant</strong> gives you the right to buy one more
                share at a fixed price (the exercise or strike price) before an
                expiry date — usually 12 to 36 months.
              </li>
              <li>
                A <strong>full warrant</strong> buys one share; a{" "}
                <strong>half warrant</strong> means two are needed for one
                share.
              </li>
            </ul>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              Warrants are a sweetener: they make the raise more attractive
              without cutting the headline price — but they also embed future
              dilution.
            </p>
          </div>

          <p className="text-slate-300 mb-8 leading-relaxed">
            This guide focuses specifically on the{" "}
            <strong className="text-gold-300">
              unit-and-warrant structure
            </strong>{" "}
            of private placements. For the wider picture of every way juniors
            raise money — bought deals, flow-through, strategic investments —
            see the pillar guide on{" "}
            <Link
              href="/guides/how-junior-mining-companies-raise-money"
              className="text-gold-400 hover:underline"
            >
              How Junior Mining Companies Raise Money
            </Link>
            .
          </p>

          <article className="prose prose-invert prose-slate max-w-none">
            {/* Section 1 */}
            <section id="what-is-a-unit" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                What is a &quot;unit&quot;?
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A private placement is a sale of securities to a select group of
                investors — typically accredited investors — rather than a
                public offering on the open market. It is the primary way
                exploration-stage juniors fund drilling, because they usually
                have no revenue and rely on equity to keep the lights on.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Rather than selling plain shares, juniors almost always package
                the raise into <strong className="text-gold-400">units</strong>.
                A unit is a bundle priced as a single security. In junior mining
                the bundle is nearly always:
              </p>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-5 my-6">
                <p className="text-slate-200 mb-0 font-mono text-sm">
                  1 unit = 1 common share + 1 warrant (or ½ warrant)
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                So when a release says &quot;the Company will issue 20,000,000
                units at $0.10 per unit for gross proceeds of $2,000,000,&quot;
                the investor is buying 20 million shares <em>and</em> 20 million
                warrants (or 10 million, if it is a half-warrant deal) for their
                money.
              </p>
            </section>

            {/* Section 2 */}
            <section id="how-warrants-work" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                How the warrant works
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A warrant is the <strong>right, not the obligation</strong>, to
                buy one additional common share at a fixed price before it
                expires. Three numbers define it:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Exercise (strike) price.
                  </strong>{" "}
                  What you pay to convert one warrant into one share — e.g.
                  $0.15. Usually set above the unit price to give the stock room
                  to run first.
                </li>
                <li>
                  <strong className="text-gold-400">Term / expiry.</strong> How
                  long the warrant is valid, measured from the closing date —
                  commonly 12, 24, or 36 months. After that it expires
                  worthless.
                </li>
                <li>
                  <strong className="text-gold-400">Coverage.</strong> How many
                  warrants come per unit — one full warrant, or one-half
                  warrant.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A warrant is <strong>in the money</strong> when the share trades
                above the exercise price, and <strong>out of the money</strong>{" "}
                when it trades below. Only in-the-money warrants get exercised —
                and when they do, the company receives fresh capital (the
                exercise price × the number of shares issued). That is why a
                healthy warrant book is a second, delayed funding source for a
                junior whose stock is performing.
              </p>
            </section>

            {/* Section 3 */}
            <section id="full-vs-half" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Full warrants vs half warrants
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                &quot;Warrant coverage&quot; is one of the fastest reads on how
                hungry a company was for capital:
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Structure
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Warrants per unit
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Signal
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        Full warrant
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 whole warrant
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Bigger sweetener; often a tougher market or a harder
                        sell
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        Half warrant
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        ½ warrant (2 needed per share)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Less dilution; common in stronger markets
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        No warrant
                      </td>
                      <td className="border border-slate-700 px-3 py-2">0</td>
                      <td className="border border-slate-700 px-3 py-2">
                        Strong demand — the company didn&apos;t need to sweeten
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                All else equal, a half-warrant deal is friendlier to existing
                shareholders because it embeds less potential future dilution
                than a full-warrant deal at the same size.
              </p>
            </section>

            {/* Section 4 — reading an announcement */}
            <section id="reading-the-announcement" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                How to read a private placement announcement
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Private placement press releases follow a near-standard
                template. Here is a typical line and how to decode it:
              </p>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-5 my-6">
                <p className="text-slate-200 mb-0 italic text-sm leading-relaxed">
                  &quot;The Company intends to complete a non-brokered private
                  placement of up to 15,000,000 units at a price of $0.10 per
                  unit for gross proceeds of up to $1,500,000. Each unit
                  comprises one common share and one-half of one common share
                  purchase warrant. Each whole warrant is exercisable at $0.15
                  for a period of 24 months from closing.&quot;
                </p>
              </div>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Non-brokered</strong> — no
                  investment bank is running it; the company placed it directly
                  (lower fees, but often a sign of a smaller raise).
                </li>
                <li>
                  <strong className="text-gold-400">
                    15,000,000 units at $0.10
                  </strong>{" "}
                  — size and price; $1.5M raised, 15M new shares.
                </li>
                <li>
                  <strong className="text-gold-400">
                    one-half of one warrant
                  </strong>{" "}
                  — 7.5M warrants total (half of 15M units).
                </li>
                <li>
                  <strong className="text-gold-400">
                    exercisable at $0.15 for 24 months
                  </strong>{" "}
                  — the warrants pay the company another $0.15/share if the
                  stock clears $0.15 within two years.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Watch also for a <strong>finder&apos;s fee</strong> or{" "}
                <strong>agent&apos;s / broker warrants</strong> (compensation to
                whoever arranged the deal), a{" "}
                <strong>four-month statutory hold period</strong> on Canadian
                placements, and any <strong>acceleration clause</strong> that
                lets the company force early warrant exercise if the stock runs.
              </p>
            </section>

            {/* Section 5 — recent announcements (serves the "announcement" intent) */}
            <section id="recent-announcements" className="mb-16">
              <div className="bg-gradient-to-br from-gold-500/10 to-amber-500/10 border border-gold-500/30 rounded-xl p-8">
                <h2 className="text-2xl font-bold text-gold-400 mb-3">
                  Find recent private placements with warrants
                </h2>
                <p className="text-slate-300 mb-4">
                  We track live and recently-closed junior mining financings —
                  including their unit structure and warrant terms — and publish
                  a weekly roundup of everything announced across gold, silver,
                  copper, lithium, and critical minerals.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/open-financings"
                    className="inline-flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-slate-900 font-bold px-5 py-2.5 rounded-lg transition-colors"
                  >
                    Live open financings →
                  </Link>
                  <Link
                    href="/reports/financings"
                    className="inline-flex items-center gap-2 border border-gold-500/40 text-gold-300 hover:bg-gold-500/10 font-semibold px-5 py-2.5 rounded-lg transition-colors"
                  >
                    Weekly financing roundup →
                  </Link>
                </div>
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
              <h2 className="text-3xl font-bold text-gold-400 mb-4">Related</h2>
              <ul className="space-y-3">
                <li>
                  <Link
                    href="/guides/how-junior-mining-companies-raise-money"
                    className="text-gold-400 hover:underline"
                  >
                    How Junior Mining Companies Raise Money (Pillar Guide) →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/open-financings"
                    className="text-gold-400 hover:underline"
                  >
                    Live Open Financings →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/reports/financings"
                    className="text-gold-400 hover:underline"
                  >
                    Weekly Financing Roundup →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/glossary"
                    className="text-gold-400 hover:underline"
                  >
                    Mining Glossary (Private Placement, Warrant, Flow-Through) →
                  </Link>
                </li>
              </ul>
            </section>
          
            <RelatedResources
              slugs={["warrant-radar","dilution-tracker","financing-flow"]} extra={[OPEN_FINANCINGS, CLOSED_FINANCINGS]}
              intro="Warrant overhang and dilution are measurable rather than guessed at. These do the measuring:"
            />
          </article>
        </div>
      </div>
    </>
  );
}
