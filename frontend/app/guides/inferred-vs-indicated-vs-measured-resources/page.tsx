import type { Metadata } from "next";
import Link from "next/link";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/inferred-vs-indicated-vs-measured-resources";

export const metadata: Metadata = {
  title: "Inferred vs Indicated vs Measured Resources: What's the Difference?",
  description:
    "The three NI 43-101 resource categories explained simply. What drill spacing makes the difference, why Inferred Resources can't be used in PFS or DFS, and how to read a category-mixed resource table.",
  keywords: [
    "inferred vs indicated resource",
    "indicated vs measured resource",
    "NI 43-101 resource categories",
    "mineral resource categories explained",
    "what is an inferred resource",
    "what is an indicated resource",
    "what is a measured resource",
    "resource to reserve conversion",
    "CIM resource definitions",
  ],
  openGraph: {
    title:
      "Inferred vs Indicated vs Measured Resources: The Difference, Explained",
    description:
      "The three NI 43-101 resource categories side-by-side, what drill spacing produces each, and the conversion ladder to Probable and Proven Reserves.",
    type: "article",
    url: CANONICAL,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Inferred vs Indicated vs Measured Resources Explained",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Inferred vs Indicated vs Measured Resources — Explained Simply",
    description:
      "The three NI 43-101 resource categories: what drill spacing produces each, and why the mix matters more than the headline number.",
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
    "Inferred vs Indicated vs Measured Resources: What's the Difference?",
  description:
    "The three NI 43-101 resource categories explained — what drill spacing produces each, the conversion ladder to reserves, and how the mix changes a deposit's investment profile.",
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
    { "@type": "DefinedTerm", name: "Inferred Mineral Resource" },
    { "@type": "DefinedTerm", name: "Indicated Mineral Resource" },
    { "@type": "DefinedTerm", name: "Measured Mineral Resource" },
  ],
  isPartOf: {
    "@type": "WebPage",
    "@id":
      "https://juniorminingintelligence.com/guides/how-to-read-ni-43-101-report",
  },
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is the difference between Inferred, Indicated, and Measured resources?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "The three categories represent increasing geological confidence based on drill spacing. Inferred Resources have the lowest confidence — drill spacing is wide enough that grade and continuity are estimated rather than known. Indicated Resources have moderate confidence — drill spacing supports preliminary mine planning. Measured Resources have the highest confidence — drill spacing is dense enough to support detailed production planning. The exact spacing varies by deposit style, but a rule of thumb is that Inferred uses 50-100m grids, Indicated 25-50m, and Measured under 25m.",
      },
    },
    {
      "@type": "Question",
      name: "Can Inferred Resources be used in a feasibility study?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "No. NI 43-101 explicitly prohibits using Inferred Resources in Pre-Feasibility Studies (PFS) or Definitive Feasibility Studies (DFS). Inferred Resources CAN be used in a Preliminary Economic Assessment (PEA), but only with a mandatory disclaimer that 'there is no certainty that the preliminary economic assessment will be realised.' For PFS and DFS, only Indicated and Measured Resources count.",
      },
    },
    {
      "@type": "Question",
      name: "What percentage of Inferred Resources actually convert to Indicated?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Conversion rates vary by deposit type and the quality of the original estimate, but historical industry experience suggests a meaningful fraction of Inferred ounces is lost during conversion — sometimes 20-40% or more. Some Inferred ounces upgrade cleanly, some are reclassified at lower grades, and some disappear entirely when infill drilling reveals the deposit is smaller or less continuous than initially modeled. Treating Inferred as 'almost Indicated' is the single most common retail-investor mistake.",
      },
    },
    {
      "@type": "Question",
      name: "How do resource categories convert to reserves?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Under NI 43-101 and the CIM Definition Standards, Indicated Resources can convert to Probable Reserves, and Measured Resources can convert to Proven Reserves — provided a Pre-Feasibility or Definitive Feasibility Study demonstrates economic viability. Inferred Resources cannot convert to reserves at all without first upgrading to Indicated or Measured through additional drilling. The conversion is also conditional on economics: even Measured Resources at uneconomic grades or in marginal jurisdictions may not convert to reserves.",
      },
    },
    {
      "@type": "Question",
      name: "Why are resource categories grouped 'M+I' but Inferred reported separately?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "NI 43-101 and the CIM standards specifically require that Inferred Resources be reported separately from Measured + Indicated. The M+I total represents the resource that could potentially be converted to reserves through economic study. Inferred is the geological hypothesis that has not yet reached that bar. Companies that headline a single 'global resource' number without breaking out the Inferred portion are doing marketing, not compliant disclosure — always check Item 14 of the technical report for the breakdown.",
      },
    },
    {
      "@type": "Question",
      name: "Is a 5 g/t Indicated Resource better than a 5 g/t Inferred Resource?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Yes, materially. The grades may be identical on paper, but the Indicated tonnage is far more likely to actually exist as represented after additional drilling. Indicated Resources can also be used in PFS/DFS and converted to reserves, while Inferred cannot. For investment purposes, a smaller Indicated deposit is often worth more than a larger Inferred one at the same grade — because Indicated has cleared the geological-confidence bar that Inferred has not.",
      },
    },
  ],
};

export default function InferredIndicatedMeasuredGuide() {
  return (
    <>
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
                  Inferred vs Indicated vs Measured Resources
                </li>
              </ol>
            </nav>

            <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              Inferred vs Indicated vs Measured Resources
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              The three NI 43-101 resource categories explained. What drill
              spacing produces each, why the conversion ladder matters, and how
              to read a category-mixed resource table.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: May 28, 2026</span>
              <span>9 min read</span>
              <span>2,300 words</span>
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
              The three categories rank a mineral resource by{" "}
              <strong className="text-gold-400">geological confidence</strong>,
              which is driven by drill-hole density:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-slate-200">
              <li>
                <strong className="text-slate-300">Inferred</strong> — lowest
                confidence. Sparse drilling. Cannot be used in PFS or DFS.
                Cannot be converted to reserves.
              </li>
              <li>
                <strong className="text-gold-400">Indicated</strong> — moderate
                confidence. Enough drilling for preliminary mine planning.
                Converts to <em>Probable Reserves</em>.
              </li>
              <li>
                <strong className="text-emerald-300">Measured</strong> — highest
                confidence. Dense drilling. Converts to <em>Proven Reserves</em>
                .
              </li>
            </ul>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              The single most common retail mistake is treating these categories
              as additive. A &quot;5 million ounce&quot; resource that is 80%
              Inferred is a very different deposit than one that is 80% Measured
              + Indicated.
            </p>
          </div>

          <p className="text-slate-300 mb-6 leading-relaxed">
            This piece is a focused deep-dive on resource categorisation. If you
            want the full context of how categories fit into the NI 43-101
            standard — including reserves, the QP role, and how to read a
            technical report end-to-end — start with our pillar guide:{" "}
            <Link
              href="/guides/how-to-read-ni-43-101-report"
              className="text-gold-400 hover:underline"
            >
              How to Read an NI 43-101 Report
            </Link>
            .
          </p>

          <article className="prose prose-invert prose-slate max-w-none">
            {/* Section 1 */}
            <section id="three-categories" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The three categories at a glance
              </h2>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Category
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Confidence
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Typical drill spacing
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Usable in
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Converts to
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Inferred
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Lowest
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        50–100m grid+
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-yellow-300">
                        PEA only (with disclaimer)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-red-400">
                        No reserve eligibility
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Indicated
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Moderate
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        25–50m grid
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-emerald-400">
                        PEA, PFS, DFS
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Probable Reserves
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Measured
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Highest
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Under 25m grid
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-emerald-400">
                        PEA, PFS, DFS
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Proven Reserves
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed text-sm italic">
                Drill spacings shown are typical ranges, not regulatory minima.
                The Qualified Person determines what spacing is appropriate
                given deposit style. Narrow, high-grade vein deposits often
                require tighter spacing for any given category than bulk
                disseminated systems.
              </p>
            </section>

            {/* Section 2 */}
            <section id="why-drill-spacing" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Why drill spacing is the dividing line
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Mineral deposits are not uniform. Grade varies across metres or
                even centimetres. The only way to know what is between two drill
                holes is to drill more holes — or estimate. Resource
                categorisation is essentially a confidence statement about how
                much estimation versus measurement underlies any given block of
                the deposit model.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Picture a 1km × 1km mineralised zone:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  Drill it on a{" "}
                  <strong className="text-gold-400">100m × 100m grid</strong>{" "}
                  and you have 100 holes. The geometry of the deposit is roughly
                  understood. Between any two holes, grade is{" "}
                  <em>extrapolated</em>. That is Inferred.
                </li>
                <li>
                  Drill it on a{" "}
                  <strong className="text-gold-400">50m × 50m grid</strong> and
                  you have 400 holes. Continuity between holes is now reasonable
                  to assume. Mine planning can begin at a preliminary level.
                  That is Indicated.
                </li>
                <li>
                  Drill it on a{" "}
                  <strong className="text-gold-400">25m × 25m grid</strong> and
                  you have 1,600 holes. Grade is well-constrained at the
                  block-model scale. Detailed mine planning is supportable. That
                  is Measured.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The economics are obvious: a 25m grid costs 16x more in drilling
                than a 100m grid. Junior miners can rarely afford to drill an
                entire deposit to Measured spacing, so resource estimates
                typically combine all three categories, with the
                higher-confidence categories concentrated in the parts of the
                deposit drilled most densely (usually near the centre of the
                envelope or at depths planned for early mining).
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                This is also why{" "}
                <strong className="text-gold-400">infill drilling</strong> —
                drilling additional holes between existing ones — is one of the
                main catalysts for junior miners between major discoveries. A
                successful infill programme can upgrade Inferred ounces to
                Indicated, which makes them eligible for inclusion in a PFS or
                DFS economic study.
              </p>
            </section>

            {/* Section 3 */}
            <section id="conversion-ladder" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The conversion ladder
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Resource categorisation feeds directly into the reserve
                categorisation that anchors every mining feasibility study.
                Under NI 43-101 (which adopts the CIM Definition Standards), the
                conversion ladder is strict and one-directional:
              </p>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 my-6">
                <pre className="text-slate-300 font-mono text-sm overflow-x-auto">
                  {`Inferred Resource ──── (infill drilling) ────► Indicated
                                                       │
                                                       │ (economic study)
                                                       ▼
                                              Probable Reserve

Measured Resource ──── (economic study) ────► Proven Reserve`}
                </pre>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Three rules to internalise:
              </p>
              <ol className="list-decimal pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Inferred cannot skip directly to Reserve.
                  </strong>{" "}
                  It must first be upgraded to Indicated (or Measured) through
                  more drilling. Then an economic study can convert it.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Conversion to Reserve is not automatic.
                  </strong>{" "}
                  Even Measured Resources may fail to convert if the economic
                  study (using realistic metal prices, costs, and recoveries)
                  shows the material is not profitable to mine.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Reserves can shrink.
                  </strong>{" "}
                  Reserves are calculated at a specific metal price. If prices
                  fall, previously-profitable rock can fall below the cut-off
                  and reclassify back to Resource. This is why reserves get
                  &quot;restated&quot; periodically.
                </li>
              </ol>
            </section>

            {/* Section 4 */}
            <section id="conversion-losses" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Inferred ounces don&apos;t always survive
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The single most important practical fact about Inferred
                Resources is that they do not have a 1:1 conversion rate to
                Indicated. When a junior infill-drills an Inferred area, three
                things can happen:
              </p>
              <div className="grid md:grid-cols-3 gap-4 my-6">
                <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-4">
                  <h3 className="text-base font-bold text-emerald-300 mb-2">
                    Clean upgrade
                  </h3>
                  <p className="text-slate-300 text-sm">
                    Infill drilling confirms grade and continuity. Ounces
                    transfer cleanly from Inferred to Indicated. Resource grows
                    or stays flat.
                  </p>
                </div>
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                  <h3 className="text-base font-bold text-yellow-300 mb-2">
                    Partial upgrade
                  </h3>
                  <p className="text-slate-300 text-sm">
                    Some areas confirm, others come in below modeled grade. Net
                    result is fewer ounces in Indicated than were in Inferred.
                    The most common outcome.
                  </p>
                </div>
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                  <h3 className="text-base font-bold text-red-300 mb-2">
                    Failed conversion
                  </h3>
                  <p className="text-slate-300 text-sm">
                    Infill reveals discontinuity, lower grades, or geometric
                    issues. Material fails the Indicated bar and stays Inferred
                    — or is removed entirely.
                  </p>
                </div>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Specific conversion rates vary enormously by deposit type.
                Bulk-tonnage porphyry systems with consistent grades convert
                well. Narrow-vein gold deposits with high grade variability
                often convert poorly. Junior managements rarely highlight
                conversion losses in press releases, so it falls to the investor
                to track them across consecutive resource updates.
              </p>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-6 my-6">
                <h3 className="text-lg font-bold text-gold-400 mb-2">
                  How to spot conversion problems
                </h3>
                <p className="text-slate-300 mb-3">
                  Compare two resource updates for the same project:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-slate-300 text-sm">
                  <li>
                    Did total tonnes grow in line with new drilling, or shrink?
                  </li>
                  <li>Did average grade hold up, or fall meaningfully?</li>
                  <li>
                    What proportion of the previously-Inferred resource is now
                    Indicated? Below 60% conversion is a yellow flag; below 40%
                    is a red flag worth investigating.
                  </li>
                </ul>
              </div>
            </section>

            {/* Section 5 */}
            <section id="pea-uses-inferred" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Why PEAs can use Inferred but PFS and DFS cannot
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                This rule trips up a lot of new investors. The logic is
                proportional to how the studies are used:
              </p>
              <ul className="list-disc pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  A{" "}
                  <strong className="text-gold-400">
                    Preliminary Economic Assessment (PEA)
                  </strong>{" "}
                  is a scoping study with ±30% accuracy. It is meant to answer
                  &quot;is this project worth taking further?&quot; — not
                  &quot;is this project bankable?&quot; Inferred Resources are
                  allowed because the whole exercise is preliminary.
                </li>
                <li>
                  A{" "}
                  <strong className="text-gold-400">
                    Pre-Feasibility Study (PFS)
                  </strong>{" "}
                  is meant to be the basis for declaring reserves and beginning
                  financing discussions. The economic case must rest on
                  resources whose geometry and grade are reasonably established.
                  Inferred Resources don&apos;t clear that bar.
                </li>
                <li>
                  A{" "}
                  <strong className="text-gold-400">
                    Definitive Feasibility Study (DFS)
                  </strong>{" "}
                  is bankable. Construction lenders rely on it. Including
                  Inferred Resources would inject risk that the rock that
                  appears in the financial model may not actually exist.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The required PEA disclaimer captures the spirit of the rule
                exactly: &quot;The PEA is preliminary in nature, includes
                Inferred mineral resources that are considered too speculative
                geologically to have the economic considerations applied that
                would enable them to be categorised as mineral reserves, and
                there is no certainty that the preliminary economic assessment
                will be realised.&quot; If a project&apos;s entire economic case
                rests on the PEA, you are betting that future drilling upgrades
                the Inferred portion — and that is a real bet, not a rounding
                error.
              </p>
            </section>

            {/* Section 6 */}
            <section id="reading-the-table" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                How to read a category-mixed resource table
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Here is a table from a hypothetical gold deposit. The headline
                press release would probably round this to &quot;a 4 million
                ounce gold project.&quot;
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Category
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Tonnes (Mt)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Grade (g/t Au)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Contained Oz
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        % of Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Measured
                      </td>
                      <td className="border border-slate-700 px-3 py-2">5</td>
                      <td className="border border-slate-700 px-3 py-2">
                        2.20
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        354,000
                      </td>
                      <td className="border border-slate-700 px-3 py-2">9%</td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Indicated
                      </td>
                      <td className="border border-slate-700 px-3 py-2">22</td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.55
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1,096,000
                      </td>
                      <td className="border border-slate-700 px-3 py-2">28%</td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        M + I
                      </td>
                      <td className="border border-slate-700 px-3 py-2">27</td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.67
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1,450,000
                      </td>
                      <td className="border border-slate-700 px-3 py-2">37%</td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Inferred
                      </td>
                      <td className="border border-slate-700 px-3 py-2">52</td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.46
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        2,440,000
                      </td>
                      <td className="border border-slate-700 px-3 py-2">63%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Three observations a careful reader would make:
              </p>
              <ol className="list-decimal pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    The project is 63% Inferred by ounces.
                  </strong>{" "}
                  The headline &quot;4 million ounces&quot; is geologically
                  honest, but the M+I number — 1.45 Moz — is what an economic
                  study can actually use today. The other 2.44 Moz is a
                  drilling-budget hypothesis.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Grade is highest in Measured and falls through Inferred.
                  </strong>{" "}
                  This is the typical pattern — denser drilling concentrates in
                  the best parts of the deposit first. As infill expands, the
                  average grade often drifts down. Modeling future resource
                  growth at the current Measured grade is wrong; the Inferred
                  grade is the realistic ceiling.
                </li>
                <li>
                  <strong className="text-gold-400">
                    A PFS on this project could use 1.45 Moz; a PEA could use
                    the full 3.9 Moz.
                  </strong>{" "}
                  If the company has only published a PEA, the economics reflect
                  a world where the Inferred ounces survive. They might not.
                </li>
              </ol>
              <p className="text-slate-300 mb-4 leading-relaxed">
                For a complete walkthrough of how this fits into the broader NI
                43-101 report — including economic studies, the Qualified Person
                system, and red flags to watch for — see our pillar guide on{" "}
                <Link
                  href="/guides/how-to-read-ni-43-101-report"
                  className="text-gold-400 hover:underline"
                >
                  How to Read an NI 43-101 Report
                </Link>
                .
              </p>
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

            {/* CTA — second link up to Pillar 1 */}
            <section className="mb-16">
              <div className="bg-gradient-to-br from-gold-500/10 to-amber-500/10 border border-gold-500/30 rounded-xl p-8">
                <h2 className="text-2xl font-bold text-gold-400 mb-3">
                  Keep going
                </h2>
                <p className="text-slate-300 mb-4">
                  Resource categories are one part of a larger system. The full
                  pillar guide covers the 27-item NI 43-101 structure, the 5
                  sections that matter most, Qualified Persons, the PEA/PFS/DFS
                  hierarchy, and 10 red flags that signal a weak report.
                </p>
                <Link
                  href="/guides/how-to-read-ni-43-101-report"
                  className="inline-flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-slate-900 font-bold px-6 py-3 rounded-lg transition-colors"
                >
                  Read: How to Read an NI 43-101 Report →
                </Link>
              </div>
            </section>

            {/* Related */}
            <section className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">Related</h2>
              <ul className="space-y-3">
                <li>
                  <Link
                    href="/guides/how-to-read-ni-43-101-report"
                    className="text-gold-400 hover:underline"
                  >
                    How to Read an NI 43-101 Report (Pillar Guide) →
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
                    href="/investor-tools/ni43-101-analyzer"
                    className="text-gold-400 hover:underline"
                  >
                    NI 43-101 Analyzer (Tool) →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/glossary"
                    className="text-gold-400 hover:underline"
                  >
                    Mining Glossary — 60 essential terms →
                  </Link>
                </li>
              </ul>
            </section>
          </article>
        </div>
      </div>
    </>
  );
}
