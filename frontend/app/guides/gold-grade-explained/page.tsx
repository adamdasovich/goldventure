import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/SiteNav";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/gold-grade-explained";

export const metadata: Metadata = {
  title:
    "Gold Grade Explained: g/t, oz/t, ppm, and What Counts as 'High Grade'",
  description:
    "What gold grade actually means. g/t vs oz/t vs ppm conversions, the historical decline in mined grades, what 'high grade' means today by mining method, and why grade alone doesn't make a deposit economic.",
  keywords: [
    "what is high grade gold",
    "gold grade explained",
    "g/t gold meaning",
    "oz/t gold conversion",
    "high grade vs low grade gold",
    "gold ppm to g/t",
    "average gold grade",
    "bonanza grade gold",
    "what is a good gold grade",
    "gold mining grade chart",
  ],
  openGraph: {
    title:
      "Gold Grade Explained: g/t, oz/t, ppm & What 'High Grade' Really Means",
    description:
      "The unit conversions, the grade tiers by mining method, and why a 'high grade' deposit isn't automatically a good investment.",
    type: "article",
    url: CANONICAL,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Gold Grade Explained",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Gold Grade Explained — g/t, oz/t, ppm & 'High Grade'",
    description:
      "Unit conversions, modern grade tiers, and why grade alone doesn't make a deposit economic.",
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
    "Gold Grade Explained: g/t, oz/t, ppm, and What Counts as 'High Grade'",
  description:
    "What gold grade actually means: unit conversions, grade tiers by mining method, historical context, and why grade alone doesn't make a deposit economic.",
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
    { "@type": "Thing", name: "Gold Mining" },
    { "@type": "Thing", name: "Mineral Grade" },
  ],
  isPartOf: {
    "@type": "WebPage",
    "@id":
      "https://juniorminingintelligence.com/guides/how-to-interpret-mining-drill-results",
  },
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What does g/t mean in gold mining?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "g/t means grams of gold per tonne of rock. It is the standard concentration unit for precious metals in modern mining. One g/t equals one part per million (ppm). For context: a typical wedding ring contains about 4-5 grams of gold; you would need to mine an entire tonne of 4 g/t rock to recover that same amount.",
      },
    },
    {
      "@type": "Question",
      name: "What is a good gold grade?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "What counts as 'good' depends on the mining method. For modern open-pit mines, 1.0-1.5 g/t Au is considered good economic grade — anything below 0.5 g/t is generally sub-economic except in very large bulk-tonnage operations. For underground mines, 5-8 g/t is good and 10+ g/t is excellent. Historical mines often worked grades 10-50x higher than modern operations because they exploited only the richest veins.",
      },
    },
    {
      "@type": "Question",
      name: "How do you convert oz/t to g/t?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "1 troy ounce per short ton (oz/t) equals approximately 34.29 g/t. The exact math: 1 troy ounce = 31.1035 grams, and 1 short ton = 907.185 kg = 907.185 tonnes/1000, so 31.1035 g / 0.907185 t = 34.286 g/t. Older US-style mining publications used oz/t; modern international standards almost exclusively use g/t. Watch for ambiguity — 'oz/t' sometimes means troy ounce per long ton (2,240 lb) or even per metric tonne, which gives different conversions. Reputable reports specify the ton type explicitly.",
      },
    },
    {
      "@type": "Question",
      name: "What is bonanza grade gold?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Bonanza grade is an informal term for exceptional gold concentrations, typically above 30 g/t and often used for grades above 100 g/t. The term comes from the Spanish word for prosperity and was adopted during the California Gold Rush. Historical bonanza mines like the Comstock Lode (Nevada) and Cripple Creek (Colorado) produced ore averaging hundreds of g/t. Modern bonanza intercepts in drill results get heavy press coverage but are typically narrow — a single 5m bonanza intercept does not guarantee a mineable deposit.",
      },
    },
    {
      "@type": "Question",
      name: "Why have gold grades dropped over time?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "The world's high-grade gold deposits have been preferentially mined out over the last 150 years. Early gold rushes worked surface oxide veins grading 30+ g/t. As those were exhausted, the industry moved to underground vein systems at 5-15 g/t. As those depleted, modern mining shifted to bulk-tonnage open-pit operations at 1-2 g/t made economic by industrial-scale earthmoving and heap-leach processing. The average grade of gold mined globally has fallen from approximately 10-20 g/t in the early 1900s to roughly 1.2-1.5 g/t today. This is not a sign that exploration has failed — it is a sign that mining technology has gotten dramatically better at processing low-grade rock.",
      },
    },
    {
      "@type": "Question",
      name: "Is high-grade gold always better than low-grade?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "No. Grade is one variable among several. A 1 g/t deposit hosting 10 million ounces in a mining-friendly jurisdiction may be vastly more valuable than a 30 g/t deposit hosting 50,000 ounces in a politically risky one. High grade often means narrow widths, underground mining, and limited mine life. Low grade in bulk tonnage means open-pit, longer mine life, lower operating risk per ounce. The best-performing gold mines historically have not always been the highest grade — they have been the ones with the right combination of grade, tonnage, mining method, and jurisdiction.",
      },
    },
    {
      "@type": "Question",
      name: "What is gold-equivalent (AuEq) grade?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Gold-equivalent grade is a calculation used in poly-metallic deposits to combine the value of multiple metals (gold, silver, copper, etc.) into a single comparable grade expressed as g/t Au. The calculation uses assumed metal prices and recovery rates to convert non-gold metal content into 'gold-equivalent' grams. A '2 g/t AuEq' deposit might be 1.0 g/t actual gold plus 30 g/t silver and 0.2% copper, all converted at assumed prices. The honesty of AuEq depends on the assumptions disclosed — if a release uses $2,400/oz gold and the current spot price is $2,100/oz, the AuEq figure is inflated. Always check the assumption footnote.",
      },
    },
  ],
};

export default function GoldGradeExplainedGuide() {
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
                <li className="text-slate-300">Gold Grade Explained</li>
              </ol>
            </nav>

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              Gold Grade Explained
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              What g/t, oz/t, and ppm actually mean. What &quot;high grade&quot;
              looks like by mining method. Why a 30 g/t deposit can be worth
              less than a 1 g/t deposit.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: May 28, 2026</span>
              <span>9 min read</span>
              <span>2,200 words</span>
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
              Gold grade is the concentration of gold in rock, almost always
              measured in{" "}
              <strong className="text-gold-400">grams per tonne</strong> (g/t).
              One g/t equals one part per million.
            </p>
            <p className="text-slate-200 mb-3">
              What counts as &quot;high grade&quot; depends on the mining
              method:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-slate-200">
              <li>
                <strong>Open-pit:</strong> sub-economic below 0.5 g/t, good at
                1.5–3 g/t, high grade above 3 g/t.
              </li>
              <li>
                <strong>Underground:</strong> sub-economic below 2 g/t, good at
                5–8 g/t, high grade above 10 g/t.
              </li>
              <li>
                <strong>Bonanza:</strong> 30+ g/t (informal, mostly used in
                historical or narrow-vein contexts).
              </li>
            </ul>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              Grade alone does not make a deposit economic. A high-grade narrow
              vein with 50,000 ounces is often less valuable than a low-grade
              bulk-tonnage deposit with 10 million ounces.
            </p>
          </div>

          <p className="text-slate-300 mb-8 leading-relaxed">
            This piece is a focused deep-dive on gold grade as a concept. For
            the broader context of how grade fits into reading a drill press
            release — including width, depth, intercept types, and the 10
            press-release tricks to watch for — see our pillar guide on{" "}
            <Link
              href="/guides/how-to-interpret-mining-drill-results"
              className="text-gold-400 hover:underline"
            >
              How to Read Mining Drill Results
            </Link>
            .
          </p>

          <article className="prose prose-invert prose-slate max-w-none">
            {/* Section 1 — Units */}
            <section id="units" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The units: g/t, ppm, oz/t, and ppb
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Gold grade gets reported in several units depending on the era
                and the region of the publication. The math is simple but worth
                knowing because press releases occasionally switch units within
                a single document.
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Unit
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        What it means
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Conversion
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Where you see it
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        g/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        grams per tonne
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Reference unit
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Modern international standard
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        ppm
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        parts per million
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 ppm = 1 g/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Geochemistry, trace elements
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        oz/t (short)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        troy oz per short ton (2,000 lb)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 oz/t ≈ 34.29 g/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Older US-style reports
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        oz/t (long)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        troy oz per long ton (2,240 lb)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 oz/t ≈ 30.61 g/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Older UK/Commonwealth reports
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        ppb
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        parts per billion
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1,000 ppb = 1 g/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Surface samples, soil geochem
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Two unit traps worth knowing:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    &quot;oz/t&quot; is ambiguous without ton-type disclosure.
                  </strong>{" "}
                  A short ton, long ton, and metric tonne all differ. A serious
                  report specifies which. If a release writes &quot;0.5 oz/t
                  Au&quot; without context, the most common modern
                  interpretation is short ton — but if you are comparing to
                  current g/t numbers, confirm.
                </li>
                <li>
                  <strong className="text-gold-400">
                    ppb headlines hide low grades.
                  </strong>{" "}
                  A press release announcing &quot;850 ppb gold from a surface
                  sample&quot; is reporting 0.85 g/t — below the economic floor
                  for most open-pit projects. ppb is a legitimate unit for
                  pathfinder geochemistry and early reconnaissance work, but if
                  ppb shows up in a hype-toned release it is usually because the
                  equivalent g/t number sounds unimpressive.
                </li>
              </ul>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-5 my-6">
                <h3 className="text-base font-bold text-gold-400 mb-2">
                  A useful mental anchor
                </h3>
                <p className="text-slate-300 mb-0 text-sm">
                  A standard wedding ring contains about 4–5 grams of gold. A
                  drill intercept of &quot;4 g/t over 50m&quot; means that for
                  every tonne of rock in that 50m intercept, you would recover
                  the gold content of one wedding ring. Scale it across the
                  volume of an entire deposit and you get to millions of ounces
                  from low-grade rock.
                </p>
              </div>
            </section>

            {/* Section 2 — Grade by Mining Method */}
            <section id="grade-by-method" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                What &quot;high grade&quot; means by mining method
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                There is no universal definition of &quot;high grade.&quot; The
                threshold depends entirely on how the deposit will be mined. The
                same grade can be marginal in one context and excellent in
                another.
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Method
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Sub-economic
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Marginal
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Good
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        High grade
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold text-left">
                        Heap leach
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 0.3
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.3 – 0.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.5 – 1.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &gt; 1.0
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold text-left">
                        Open-pit + mill
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 0.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.5 – 0.8
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.0 – 3.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &gt; 3.0
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold text-left">
                        Underground
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 2
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        2 – 3
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        5 – 10
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &gt; 10
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold text-left">
                        Narrow-vein UG
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        5 – 8
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        10 – 30
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &gt; 30 (bonanza)
                      </td>
                    </tr>
                  </tbody>
                </table>
                <p className="text-xs text-slate-500 italic mt-1">
                  Thresholds are rules of thumb at current gold prices
                  (~$2,100/oz) and assume mining-friendly jurisdictions. Costs
                  vary materially by location, depth, and strip ratio.
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Why the same g/t means different things:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Heap leach</strong> uses
                  crushed ore stacked on pads and percolated with cyanide
                  solution. Operating costs are very low, but recovery is also
                  lower (60–75% for oxide ore). Economic at very low grades
                  because of the cheap process.
                </li>
                <li>
                  <strong className="text-gold-400">Open-pit + mill</strong>{" "}
                  uses conventional crushing, grinding, and flotation/cyanide
                  leaching. Higher cost per tonne but higher recovery (~90%+).
                  Needs more grade to cover the processing cost.
                </li>
                <li>
                  <strong className="text-gold-400">Underground</strong>{" "}
                  operations cost 2–4x more per tonne than open-pit because you
                  have to drive shafts, ventilate, dewater, and selectively mine
                  smaller volumes. Needs proportionally more grade to be
                  economic.
                </li>
                <li>
                  <strong className="text-gold-400">Narrow-vein</strong>{" "}
                  underground operations are the most expensive per tonne
                  because the production rates are very low. Only feasible for
                  very high grades — historically bonanza grades.
                </li>
              </ul>
            </section>

            {/* Section 3 — Historical Context */}
            <section id="historical-context" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Historical vs modern grades — why the bar keeps moving
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Anyone reading old mining history is struck by how absurd the
                grades sound compared to modern numbers. The Comstock Lode in
                Nevada produced ore averaging hundreds of g/t in its early
                years. The Witwatersrand in South Africa worked grades of 8–15
                g/t for nearly a century. California Gold Rush placer miners
                panned grades that today would be considered surreal.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The world average grade of mined gold has fallen roughly 10-fold
                over the last 150 years:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Early 1900s:</strong> global
                  average mined grade roughly 10–20 g/t. The richest surface and
                  shallow oxide deposits were being worked.
                </li>
                <li>
                  <strong className="text-gold-400">Mid-1900s:</strong> roughly
                  4–8 g/t. The industry was deeper into underground vein
                  systems.
                </li>
                <li>
                  <strong className="text-gold-400">Late 1900s:</strong> roughly
                  2–3 g/t. The shift to bulk-tonnage open-pit operations (Carlin
                  Trend, Witwatersrand deep mines, Australia) made lower grades
                  economic.
                </li>
                <li>
                  <strong className="text-gold-400">2020s:</strong> roughly
                  1.2–1.5 g/t. Modern operations like Carlin Trend, Cortez,
                  Detour Lake, and Boddington average between 0.8 and 1.5 g/t.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The decline is not a failure of exploration — it is a triumph of
                mining technology. Modern earthmoving equipment, cheap cyanide
                processing, and economies of scale have made grades that would
                have been unmineable in 1900 routinely profitable today. A 1 g/t
                open-pit mine moving 100,000 tonnes a day produces more gold per
                year than most historical high-grade vein mines did at 30+ g/t —
                and at a fraction of the investment-per-ounce cost.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The implication for investors: do not anchor on historical
                grades when evaluating modern juniors. A 2026 explorer hitting 3
                g/t over 30m in an open-pittable setting has discovered
                something genuinely valuable, even though that grade would have
                been considered marginal in 1900.
              </p>
            </section>

            {/* Section 4 — Why grade isn't everything */}
            <section id="grade-isnt-everything" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Why grade isn&apos;t everything
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Six factors matter alongside grade when comparing deposits:
              </p>
              <ol className="list-decimal pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Tonnage.</strong> Total
                  contained ounces matter more than per-tonne concentration. A 1
                  g/t deposit with 10 Mt of ore (320,000 contained ounces) may
                  be worth more than a 30 g/t vein with 50,000 ounces.
                </li>
                <li>
                  <strong className="text-gold-400">Width and geometry.</strong>{" "}
                  A wide, continuous body is far easier to mine than a narrow,
                  pinch-and-swell vein at the same grade. Width determines
                  whether bulk methods can be used.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Depth and strip ratio.
                  </strong>{" "}
                  A 3 g/t deposit under 200m of waste rock is far less
                  attractive than the same deposit at surface. Strip ratios
                  above 5:1 start to hurt; above 10:1 is generally fatal for
                  open-pit economics regardless of grade.
                </li>
                <li>
                  <strong className="text-gold-400">Metallurgy.</strong>{" "}
                  Free-milling gold ore yields 90%+ recovery cheaply. Refractory
                  ore (sulphide-locked or carbon-bearing) may recover only
                  60–75% even with expensive pre-treatment. A 5 g/t refractory
                  deposit can be less economic than a 2 g/t free-milling one.
                </li>
                <li>
                  <strong className="text-gold-400">Jurisdiction.</strong>{" "}
                  Permitting, political stability, infrastructure, and tax
                  regime can swing project value by 5x. A 1.5 g/t deposit in
                  Nevada is generally worth more per ounce than a 5 g/t deposit
                  in a high-risk jurisdiction.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Resource confidence.
                  </strong>{" "}
                  A 3 g/t Inferred Resource is geologically less proven than a 2
                  g/t Indicated Resource of the same tonnage. See our{" "}
                  <Link
                    href="/guides/inferred-vs-indicated-vs-measured-resources"
                    className="text-gold-400 hover:underline"
                  >
                    Inferred vs Indicated vs Measured guide
                  </Link>{" "}
                  for why category matters as much as grade.
                </li>
              </ol>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The best gold projects historically have rarely been the
                highest-grade ones. They have been the projects with the right
                <em> combination</em> of grade, tonnage, geometry, metallurgy,
                and jurisdiction. Grade headlines drive short-term sentiment;
                the combination drives long-term valuation.
              </p>
            </section>

            {/* CTA */}
            <section className="mb-16">
              <div className="bg-gradient-to-br from-gold-500/10 to-amber-500/10 border border-gold-500/30 rounded-xl p-8">
                <h2 className="text-2xl font-bold text-gold-400 mb-3">
                  Keep going
                </h2>
                <p className="text-slate-300 mb-4">
                  Grade is one component of reading a drill press release. Width
                  matters as much. Geology terminology, intercept types, and the
                  press-release tricks that inflate ordinary results matter too.
                  The full pillar guide covers all of it with a worked example.
                </p>
                <Link
                  href="/guides/how-to-interpret-mining-drill-results"
                  className="inline-flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-slate-900 font-bold px-6 py-3 rounded-lg transition-colors"
                >
                  Read: How to Read Mining Drill Results →
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
              <h2 className="text-3xl font-bold text-gold-400 mb-4">Related</h2>
              <ul className="space-y-3">
                <li>
                  <Link
                    href="/guides/how-to-interpret-mining-drill-results"
                    className="text-gold-400 hover:underline"
                  >
                    How to Read Mining Drill Results (Pillar Guide) →
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
                    href="/guides/inferred-vs-indicated-vs-measured-resources"
                    className="text-gold-400 hover:underline"
                  >
                    Inferred vs Indicated vs Measured Resources →
                  </Link>
                </li>
                <li>
                  <Link
                    href="/investor-tools/grade-ranker"
                    className="text-gold-400 hover:underline"
                  >
                    Grade Ranker (Tool) →
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
          </article>
        </div>
      </div>
    </>
  );
}
