import type { Metadata } from "next";
import Link from "next/link";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/how-to-interpret-mining-drill-results";

export const metadata: Metadata = {
  title:
    "How to Read Mining Drill Results: Grade, Width, and Spotting the Winners",
  description:
    "A plain-English guide to reading mining drill press releases. What g/t means, why width matters as much as grade, how to spot a bonanza vs. a dud, and the press-release tricks that inflate ordinary results.",
  keywords: [
    "how to read drill results mining",
    "drill intercept explained",
    "g/t gold meaning",
    "mining assay results explained",
    "drill press release",
    "step-out vs infill drilling",
    "gold equivalent grade",
    "bonanza grade gold",
    "high grade vs low grade gold",
    "drill core sampling",
  ],
  openGraph: {
    title:
      "How to Read Mining Drill Results — Grade, Width & Spotting the Winners",
    description:
      "What g/t actually means, why width matters as much as grade, and the press-release tricks that make ordinary intercepts look spectacular.",
    type: "article",
    url: CANONICAL,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "How to Read Mining Drill Results",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "How to Read Mining Drill Results",
    description:
      "What g/t means, why width matters, and the press-release tricks to watch for.",
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
    "How to Read Mining Drill Results: Grade, Width, and Spotting the Winners",
  description:
    "A plain-English guide to reading mining drill press releases. Grade-times-width, intercept types, grade tiers by metal, geology terms a non-geologist needs, and the press-release tricks that inflate ordinary results.",
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
    { "@type": "Thing", name: "Mining Drill Results" },
    { "@type": "Thing", name: "Mineral Assay" },
    { "@type": "Thing", name: "Diamond Drilling" },
  ],
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "How do you read a mining drill result?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Every drill result has three numbers that matter: depth (where the intercept starts and ends down the hole), width (how thick the mineralised zone is), and grade (concentration of the target metal). The most important derived number is grade-times-width — a 1.0 g/t intercept over 100m and a 10 g/t intercept over 10m both produce a 'gram-metre' value of 100, but they may represent very different deposits. Always check the true width (perpendicular to the mineralised body) vs. the down-hole width, the cut-off grade applied, and whether the interval is a single high-grade hit or a composite of many intervals stitched together.",
      },
    },
    {
      "@type": "Question",
      name: "What does g/t mean in mining?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "g/t means grams per tonne. It is the standard concentration unit for precious metals in mining (gold, silver, platinum group metals). One g/t means one gram of metal in one tonne of rock — equivalent to one part per million. For gold, anything above 1 g/t is considered economic for open-pit mining at current prices, 3-5 g/t is good for underground, and 10+ g/t is high grade. Bonanza grade is loosely anything above 30 g/t. Base metals like copper and zinc are reported in percent (%) instead, since their concentrations are typically 100-1,000 times higher than precious metals.",
      },
    },
    {
      "@type": "Question",
      name: "What is a bonanza grade in gold mining?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Bonanza grade is an informal term for exceptionally high gold concentrations, generally above 30 g/t and often used for grades above 100 g/t. The term originates from the historical California and Comstock Lode mines where rare 'bonanza' veins produced astronomical grades. Modern bonanza intercepts get heavy press coverage because they signal high-grade structures that can be mined profitably even at low tonnages. However, bonanza intercepts are often narrow and erratic — they may not represent a continuous mineable zone, and a single 200 g/t hole does not guarantee a deposit.",
      },
    },
    {
      "@type": "Question",
      name: "What is the difference between true width and down-hole width?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Down-hole width is the length of the mineralised intercept measured along the drill core. True width is the actual thickness of the mineralised body measured perpendicular to its strike and dip. They are only equal when the drill hole intersects the mineralised body at a perfect 90-degree angle. In practice, holes are usually angled — so a 30m down-hole intercept might represent only 15-20m of true width. Honest press releases either disclose true width explicitly or say 'true width is estimated to be approximately X% of the down-hole length.' Marketing-first releases highlight down-hole widths and bury or omit true widths.",
      },
    },
    {
      "@type": "Question",
      name: "What is grade times width and why does it matter?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Grade times width (often called gram-metres or g·m) is the simplest way to compare drill intercepts across different widths and grades. A 5 g/t intercept over 20m gives 100 g·m, identical to a 1 g/t intercept over 100m. The metric strips out the cosmetic appeal of high-grade-narrow vs. low-grade-wide and lets you compare the actual contained metal per metre drilled. Most serious investors and geologists track gram-metres rather than headline grades. A drill program where average gram-metres are increasing over time signals an improving deposit; one where they are decreasing is the opposite — even if individual headline holes look impressive.",
      },
    },
    {
      "@type": "Question",
      name: "What is gold-equivalent (AuEq) grade?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Gold-equivalent (AuEq) is a calculated grade that converts the value of other metals in the rock (silver, copper, etc.) into the equivalent quantity of gold at assumed metal prices and recovery rates. It is used for poly-metallic deposits where multiple metals contribute to revenue. The catch: AuEq depends entirely on the assumed prices and recoveries. A press release reporting '2.5 g/t AuEq' may use $2,400/oz gold and $30/oz silver — if prices fall, AuEq falls. Always check the assumptions used in the AuEq calculation, and compare them to current spot prices. AuEq is most honest when the calculation method and assumptions are disclosed prominently.",
      },
    },
    {
      "@type": "Question",
      name: "What is the difference between step-out drilling and infill drilling?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Step-out drilling tests new ground outside the known deposit boundary — it is exploration aimed at growing the deposit. A successful step-out hole extends the mineralisation laterally or to depth and signals the deposit may be larger than previously thought. Infill drilling fills gaps between existing holes inside the known deposit — its purpose is to upgrade resource categories (Inferred to Indicated, Indicated to Measured) rather than to add new tonnes. Step-outs are higher-risk, higher-reward catalysts; infill is methodical resource confirmation. The drill program type tells you what kind of news you are reading.",
      },
    },
    {
      "@type": "Question",
      name: "What is a composite interval in a drill result?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A composite (or weighted average) interval is a single grade-width figure calculated by averaging multiple smaller intercepts within a longer down-hole range. Companies use composites to report 'overall' results, but the technique can blend high-grade and low-grade sections to make average grades look better than any continuous mineralised zone actually is. The red flag is internal dilution — a composite of '50m at 2 g/t' that breaks into '10m at 8 g/t, 30m at 0.3 g/t, 10m at 2 g/t' is not the same as 50 continuous metres at 2 g/t. Honest press releases disclose the internal breakdown beneath the composite headline. If a release reports composites only, dig into the appendix or the SEDAR+ filing for the raw intervals.",
      },
    },
    {
      "@type": "Question",
      name: "How long does it take to get drill results?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Typically 4-8 weeks from drilling to released results, though it can stretch to 3+ months during peak season when commercial assay labs are backlogged. The workflow is: drill the hole, log the core, cut and sample, ship to lab, lab does sample prep, lab assays, results come back, company reviews and (for material results) issues a press release. The delay is mostly the assay lab — independent labs like ALS, SGS, and Bureau Veritas process tens of thousands of samples per week and queue depth varies. Companies sometimes pre-release visual observations from the core ahead of assays — these can move stocks but are not yet confirmed.",
      },
    },
  ],
};

const howToSchema = {
  "@context": "https://schema.org",
  "@type": "HowTo",
  name: "How to Read a Mining Drill Press Release in 5 Minutes",
  description:
    "A focused workflow for assessing whether a drill press release is meaningful or marketing noise.",
  totalTime: "PT5M",
  step: [
    {
      "@type": "HowToStep",
      name: "Identify the headline intercept",
      text: "Find the lead number in the press release. Read it as 'X grams per tonne over Y metres from Z depth.' Note all three values before forming any opinion.",
    },
    {
      "@type": "HowToStep",
      name: "Check true width vs. down-hole width",
      text: "Look for an explicit true-width disclosure. If only down-hole width is given, mentally halve it as a rough first approximation for steeply-dipping bodies drilled at an angle.",
    },
    {
      "@type": "HowToStep",
      name: "Calculate grade times width",
      text: "Multiply grade by true width to get gram-metres. Compare to peer projects in the same metal and deposit type.",
    },
    {
      "@type": "HowToStep",
      name: "Look for internal dilution in composites",
      text: "If the headline is a composite of multiple intervals, find the breakdown. A '50m at 2 g/t' composite that is mostly waste rock with one narrow high-grade hit is a very different result from 50 continuous metres of 2 g/t.",
    },
    {
      "@type": "HowToStep",
      name: "Note whether it's a step-out, infill, or twin hole",
      text: "Step-outs grow the deposit, infill confirms it, twins verify older holes. The category determines how much weight to give the result.",
    },
    {
      "@type": "HowToStep",
      name: "Compare to the company's grade peer group",
      text: "A 1 g/t result is mediocre for open-pit gold in Nevada and excellent for porphyry copper. Context determines significance.",
    },
  ],
};

export default function DrillResultsGuide() {
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
                <li className="text-slate-300">How to Read Drill Results</li>
              </ol>
            </nav>

            <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              How to Read Mining Drill Results
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              A plain-English guide to drill press releases. What g/t means, why
              width matters as much as grade, the press-release tricks that make
              ordinary intercepts look spectacular, and how to spot the real
              winners.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: May 28, 2026</span>
              <span>18 min read</span>
              <span>4,800 words</span>
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
              Every drill result is three numbers: <strong>grade</strong>{" "}
              (concentration of metal), <strong>width</strong> (thickness of the
              mineralised zone), and <strong>depth</strong> (where the intercept
              sits). The single most important derived metric is{" "}
              <strong className="text-gold-400">grade × width</strong> (in
              gram-metres for gold) — it cuts through the marketing appeal of
              high-grade-narrow vs. low-grade-wide. To read any drill press
              release in 5 minutes:
            </p>
            <ol className="list-decimal pl-6 space-y-1 text-slate-200">
              <li>Note grade, width, depth.</li>
              <li>
                Check for <strong className="text-gold-400">true width</strong>{" "}
                (not just down-hole width).
              </li>
              <li>Compute grade × width.</li>
              <li>
                Check for{" "}
                <strong className="text-gold-400">internal dilution</strong>{" "}
                inside composites.
              </li>
              <li>Note step-out vs infill vs twin.</li>
              <li>Compare to the project&apos;s typical grade peer group.</li>
            </ol>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              Almost every weak drill result on the market today looks
              impressive at a glance. The five-minute check above filters most
              of them out.
            </p>
          </div>

          {/* TOC */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-12">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Table of Contents
            </h2>
            <ol className="space-y-2 text-slate-300 list-decimal pl-6">
              <li>
                <a href="#anatomy" className="hover:text-gold-400">
                  The anatomy of a drill result
                </a>
              </li>
              <li>
                <a href="#grade-units" className="hover:text-gold-400">
                  Grade units explained (g/t, %, ppm, oz/t)
                </a>
              </li>
              <li>
                <a href="#grade-tiers" className="hover:text-gold-400">
                  Grade tiers by metal — what counts as &quot;high grade&quot;
                </a>
              </li>
              <li>
                <a href="#width" className="hover:text-gold-400">
                  True width vs. down-hole width
                </a>
              </li>
              <li>
                <a href="#grade-x-width" className="hover:text-gold-400">
                  Grade × width and gram-metres
                </a>
              </li>
              <li>
                <a href="#intercept-types" className="hover:text-gold-400">
                  Intercept types: bonanza, zone-confirming, dud
                </a>
              </li>
              <li>
                <a href="#drill-program-types" className="hover:text-gold-400">
                  Step-out vs infill vs twin holes
                </a>
              </li>
              <li>
                <a href="#geology-terms" className="hover:text-gold-400">
                  Geology terms a non-geologist needs
                </a>
              </li>
              <li>
                <a href="#press-release-tricks" className="hover:text-gold-400">
                  The press-release tricks to watch for
                </a>
              </li>
              <li>
                <a href="#worked-example" className="hover:text-gold-400">
                  Worked example — translating a real drill table
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
            {/* Section 1 */}
            <section id="anatomy" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The anatomy of a drill result
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A drill result on a press release usually reads something like
                this:
              </p>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-5 my-4 font-mono text-sm">
                <p className="text-slate-200 mb-0">
                  Hole NQ-26-184 intersected{" "}
                  <strong className="text-gold-400">
                    24.8 metres grading 3.42 g/t Au
                  </strong>{" "}
                  from <strong className="text-gold-400">142.5 m</strong> depth,
                  including{" "}
                  <strong className="text-gold-400">
                    4.2 m at 12.6 g/t Au
                  </strong>{" "}
                  from 156.1 m. True width is estimated at approximately 85% of
                  down-hole length.
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                That single sentence contains all six pieces of information you
                need:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Hole ID</strong> (NQ-26-184)
                  — lets you cross-reference with project maps and prior
                  releases. The format is usually a project code + year + hole
                  number.
                </li>
                <li>
                  <strong className="text-gold-400">Width</strong> (24.8 m) —
                  how thick the mineralised intercept is, measured along the
                  drill core.
                </li>
                <li>
                  <strong className="text-gold-400">Grade</strong> (3.42 g/t Au)
                  — average concentration of gold across that width.
                </li>
                <li>
                  <strong className="text-gold-400">Depth</strong> (from 142.5
                  m) — where the intercept starts down the hole. Tells you
                  whether the mineralization is shallow (favourable for
                  open-pit) or deep (underground only).
                </li>
                <li>
                  <strong className="text-gold-400">Internal high-grade</strong>{" "}
                  (4.2 m at 12.6 g/t) — a higher-grade section within the
                  broader intercept. Companies often highlight these because
                  they look impressive.
                </li>
                <li>
                  <strong className="text-gold-400">True width estimate</strong>{" "}
                  (~85% of down-hole length) — the geometric correction
                  discussed in detail below. The fact that this release
                  discloses it explicitly is a good sign.
                </li>
              </ul>
            </section>

            {/* Section 2 */}
            <section id="grade-units" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Grade units explained
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Mining uses several grade units depending on the metal and the
                concentration involved. Knowing how they relate matters because
                press releases sometimes switch units within a single document.
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Unit
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Means
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Typical for
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Conversion
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
                        Au, Ag, Pt, Pd
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 g/t = 1 ppm
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
                        Same as g/t, used for trace elements
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 ppm = 1 g/t
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        %
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        percent by weight
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Cu, Zn, Pb, Ni, Li (as Li₂O), Fe
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1% = 10,000 g/t = 10,000 ppm
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        oz/t
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        troy ounces per short ton
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Au (US-style; less common in modern releases)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1 oz/t ≈ 34.3 g/t
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
                        Au (very early-stage sampling, soil geochem)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1,000 ppb = 1 g/t
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-mono">
                        TREO
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        total rare earth oxide %
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Rare earths (REE)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        Reported as % of contained oxides
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Two unit-related traps to watch:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Surface samples in ppb.
                  </strong>{" "}
                  An early-stage explorer reporting &quot;rock chip sample
                  graded 800 ppb gold&quot; is reporting 0.8 g/t — well below
                  any economic threshold. Some press releases lean on ppb
                  because the number looks bigger.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Lithium reported as Li, Li₂O, or LCE.
                  </strong>{" "}
                  Lithium can be reported as elemental Li, as the oxide Li₂O, or
                  as lithium carbonate equivalent (LCE). The same deposit
                  produces three very different headline numbers. 1% Li₂O is
                  approximately 0.47% Li, and approximately 2.47% LCE. Compare
                  apples to apples.
                </li>
              </ul>
            </section>

            {/* Section 3 — Grade Tiers */}
            <section id="grade-tiers" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Grade tiers by metal — what counts as &quot;high grade&quot;
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Grade thresholds are deposit-type and method dependent. The
                tiers below are rules of thumb for typical deposits at current
                metal prices — useful for first-pass assessment of a press
                release.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Gold (g/t Au)
              </h3>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Tier
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Open-pit
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Underground
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Sub-economic
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 0.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        &lt; 2
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Marginal
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.5 – 0.8
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        2 – 3
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Economic
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.8 – 1.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        3 – 5
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Good
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.5 – 3
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        5 – 10
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        High grade
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        3 – 10
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        10 – 30
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Bonanza
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        10+ (rare in bulk)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">30+</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Other metals (rough rules of thumb)
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Silver (g/t Ag).</strong>{" "}
                  Economic floor ~40 g/t open-pit, ~150 g/t underground. High
                  grade ~300+. Bonanza ~1,000+. The historical Comstock and
                  Cerro Rico mines averaged thousands of g/t.
                </li>
                <li>
                  <strong className="text-gold-400">Copper (% Cu).</strong>{" "}
                  Porphyry open-pit economic at ~0.4%, good at 0.7%, high grade
                  at 1%+. Underground vein-style operates above ~1.5-2%.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Zinc + Lead (% Zn+Pb combined).
                  </strong>{" "}
                  VMS and SedEx deposits typically need 6%+ combined to be
                  economic. High grade is 10%+ combined.
                </li>
                <li>
                  <strong className="text-gold-400">Nickel (% Ni).</strong>{" "}
                  Sulphide deposits economic at ~1% open-pit, 1.5%+ underground.
                  Laterites operate at lower grades (~1%) but higher tonnages.
                </li>
                <li>
                  <strong className="text-gold-400">Lithium.</strong> Hard-rock
                  spodumene economic at 1%+ Li₂O. Brine projects economic at
                  ~500 ppm Li. Clay deposits ~1,500 ppm.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Rare earths (% TREO).
                  </strong>{" "}
                  Concentration matters less than the magnet REE proportion (Nd,
                  Pr, Tb, Dy). 1% TREO with 25%+ magnet REE is more valuable
                  than 3% TREO dominated by cerium and lanthanum.
                </li>
              </ul>
            </section>

            {/* Section 4 — Width */}
            <section id="width" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                True width vs. down-hole width
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Drill holes rarely intersect a mineralised body at 90 degrees.
                Holes are typically angled to maximise core recovery and to hit
                specific geological targets. The result is that the intercept
                measured along the core is longer than the actual thickness of
                the body.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The geometry: if a mineralised vein is vertical and a hole hits
                it at 60 degrees from horizontal, an intercept measured 30m
                along the core represents only about 26m of true (vertical)
                width. As the angle gets steeper or the body more tilted, the
                gap widens. For typical drill angles and steeply-dipping bodies,
                true width is often 60-85% of down-hole width.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Why this matters for press releases:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  Down-hole widths inflate the apparent thickness of the
                  deposit. Headline numbers based on down-hole are flattering.
                </li>
                <li>
                  Honest releases either give true width directly or state the
                  approximate ratio (e.g., &quot;true width is approximately 75%
                  of intercept length&quot;).
                </li>
                <li>
                  Releases that report &quot;intercept widths&quot; without
                  clarifying down-hole vs. true width are leaning on the
                  ambiguity. Default assumption: down-hole.
                </li>
              </ul>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-5 my-6">
                <h4 className="text-base font-bold text-gold-400 mb-2">
                  Quick rule of thumb
                </h4>
                <p className="text-slate-300 mb-0 text-sm">
                  If a press release does not disclose true width, mentally
                  apply a 65-75% factor to the headline intercept length before
                  comparing to peer projects. This is rough but better than
                  treating down-hole as gospel.
                </p>
              </div>
            </section>

            {/* Section 5 — Grade x Width */}
            <section id="grade-x-width" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Grade × width and gram-metres
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The most useful single metric for comparing drill intercepts is{" "}
                <strong className="text-gold-400">grade × true width</strong>,
                usually expressed as gram-metres (g·m) for precious metals or
                metre-percent (m·%) for base metals. It collapses two variables
                into one that approximates contained metal per metre of drilling
                — the actual economic quantity.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Compare these three intercepts:
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Intercept
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Width (m)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Grade (g/t Au)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Gram-metres
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">A</td>
                      <td className="border border-slate-700 px-3 py-2">100</td>
                      <td className="border border-slate-700 px-3 py-2">1.0</td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        100
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">B</td>
                      <td className="border border-slate-700 px-3 py-2">20</td>
                      <td className="border border-slate-700 px-3 py-2">5.0</td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        100
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">C</td>
                      <td className="border border-slate-700 px-3 py-2">5</td>
                      <td className="border border-slate-700 px-3 py-2">
                        20.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        100
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                All three intercepts have identical gram-metre values. But they
                describe very different deposits:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong>Intercept A</strong> looks unimpressive in a press
                  release. 1 g/t over 100m is the signature of a bulk-tonnage
                  open-pit deposit. Boring but bankable.
                </li>
                <li>
                  <strong>Intercept B</strong> is the sweet spot for many
                  Canadian gold juniors. Wide enough for some mining method
                  flexibility, grade strong enough to attract investor
                  attention.
                </li>
                <li>
                  <strong>Intercept C</strong> is the bonanza press release.
                  Gets the strongest market reaction in the short term — but
                  whether 5m of 20 g/t represents a continuous mineable
                  structure or an isolated bonanza pocket depends on the
                  surrounding drilling. Single-hole bonanza without confirmation
                  is often a head-fake.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Gram-metres also expose press-release tactics. A company that
                cycles between releasing a high-grade-narrow intercept one
                quarter and a low-grade-wide intercept the next, both at
                comparable gram-metres, may not be advancing the deposit at all
                — just rotating which hole gets featured. Tracking gram-metres
                over time is far more informative than tracking headlines.
              </p>
            </section>

            {/* Section 6 — Intercept Types */}
            <section id="intercept-types" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Intercept types: bonanza, zone-confirming, dud
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Not every drill intercept matters the same way to the investment
                thesis. A useful informal taxonomy:
              </p>
              <div className="grid md:grid-cols-3 gap-4 my-6">
                <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-5">
                  <h3 className="text-base font-bold text-emerald-300 mb-2">
                    Bonanza / discovery
                  </h3>
                  <p className="text-slate-300 text-sm mb-2">
                    Very high grade and/or significant width in new ground.
                    Re-rates the entire project.
                  </p>
                  <p className="text-xs text-slate-400">
                    Examples: first-pass step-out hitting 30+ g/t Au; new vein
                    intercepted outside known envelope.
                  </p>
                </div>
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-5">
                  <h3 className="text-base font-bold text-yellow-300 mb-2">
                    Zone-confirming
                  </h3>
                  <p className="text-slate-300 text-sm mb-2">
                    Confirms continuity of known mineralisation at expected
                    grades. Incremental — does not re-rate the project but
                    de-risks it.
                  </p>
                  <p className="text-xs text-slate-400">
                    Examples: infill at typical project grade; step-out hitting
                    expected envelope.
                  </p>
                </div>
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-5">
                  <h3 className="text-base font-bold text-red-300 mb-2">Dud</h3>
                  <p className="text-slate-300 text-sm mb-2">
                    Below-expected grade, lost continuity, or geological
                    surprise (e.g., fault offset). Often the most informative
                    result for de-risking.
                  </p>
                  <p className="text-xs text-slate-400">
                    Examples: step-out missing the expected vein; infill coming
                    in well below modeled grade.
                  </p>
                </div>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Press releases pre-categorise results for you, but not always
                honestly. Watch for:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Negative drilling buried in unrelated releases.
                  </strong>{" "}
                  Some companies will pad a press release headlined &quot;new
                  joint venture&quot; or &quot;new appointment&quot; with
                  underwhelming drill results in the back paragraphs.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Months between drill releases.
                  </strong>{" "}
                  Drill labs take 4-8 weeks, but if results stop coming and
                  drilling has officially completed, the missing results may be
                  intentionally delayed.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Selective highlighting.
                  </strong>{" "}
                  A release that headlines &quot;Hole 5 returns 8 g/t over
                  10m&quot; while burying Holes 1-4 (all sub-1 g/t) is
                  cherry-picking. Check the appendix or SEDAR+ for the full
                  drill table.
                </li>
              </ul>
            </section>

            {/* Section 7 — Program Types */}
            <section id="drill-program-types" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Step-out vs infill vs twin holes
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The type of drilling determines what kind of catalyst the result
                represents.
              </p>
              <ul className="space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">Step-out</strong> — drilled
                  outside the known mineralised envelope to test if the deposit
                  extends. Successful step-outs grow the deposit. Higher risk,
                  higher reward. The most market-moving result type.
                </li>
                <li>
                  <strong className="text-gold-400">Infill</strong> — drilled
                  inside the known envelope between existing holes. The goal is
                  resource category upgrade (Inferred → Indicated). Lower-risk,
                  lower-reward but essential for advancing toward a feasibility
                  study. For why this matters, see{" "}
                  <Link
                    href="/guides/inferred-vs-indicated-vs-measured-resources"
                    className="text-gold-400 hover:underline"
                  >
                    Inferred vs Indicated vs Measured Resources
                  </Link>
                  .
                </li>
                <li>
                  <strong className="text-gold-400">Twin holes</strong> —
                  drilled adjacent to an existing hole (usually historical) to
                  verify earlier results. Common when a company acquires a
                  project from a previous owner. Twins that match the historical
                  result are confirmatory; twins that miss are concerning.
                </li>
                <li>
                  <strong className="text-gold-400">Scout / wildcat</strong> —
                  greenfield drilling into geophysical or geochemical targets
                  with no prior drilling. Either makes a discovery or proves the
                  target is empty. Very high variance.
                </li>
                <li>
                  <strong className="text-gold-400">Definition drilling</strong>{" "}
                  — extremely tight-spaced drilling (often 5-15m grids) ahead of
                  mining, to precisely define ore boundaries. Usually only done
                  at near-production or operating mines.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Most quality press releases identify program type explicitly. If
                a release simply says &quot;the company drilled X holes,
                including the following intercepts&quot; without clarifying
                whether it was infill, step-out, or scout drilling, that
                ambiguity is itself informative — usually because the program
                mixed types and the company is averaging across them.
              </p>
            </section>

            {/* Section 8 — Geology Terms */}
            <section id="geology-terms" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Geology terms a non-geologist needs
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Press releases routinely sprinkle in geological terminology that
                can intimidate non-specialist investors. A working vocabulary
                covers the 90% of cases you will see.
              </p>
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                {[
                  [
                    "Vein",
                    "Tabular body of minerals filling a fracture. Often high-grade but narrow. Most historical gold mines exploit vein systems.",
                  ],
                  [
                    "Stockwork",
                    "A network of small interconnected veins. Larger total volume than a single vein, but with bulk-tonnage style economics.",
                  ],
                  [
                    "Disseminated",
                    "Mineralisation spread throughout the rock rather than concentrated in veins. Lower grade, but very wide intercepts possible. Porphyry copper is the archetype.",
                  ],
                  [
                    "Porphyry",
                    "Large-tonnage, low-grade copper or copper-gold deposit type. Multi-billion-tonne porphyries underpin major copper mines globally.",
                  ],
                  [
                    "Epithermal",
                    "Gold and silver deposits formed near surface by hot fluids. Classic high-grade vein style. Most Latin American and Pacific Rim gold districts are epithermal.",
                  ],
                  [
                    "Orogenic",
                    "Gold deposits associated with deeply-formed structures during mountain building. The Abitibi gold belt in Canada is the textbook orogenic gold district.",
                  ],
                  [
                    "VMS",
                    "Volcanogenic Massive Sulphide — base metal (zinc, lead, copper, silver) deposits formed by submarine hydrothermal activity. Often polymetallic.",
                  ],
                  [
                    "SedEx",
                    "Sediment-hosted exhalative deposits. Large stratabound zinc-lead-silver deposits. Red Dog and Broken Hill are famous examples.",
                  ],
                  [
                    "IOCG",
                    "Iron Oxide-Copper-Gold. A large, often polymetallic deposit type. Olympic Dam in Australia is the archetype.",
                  ],
                  [
                    "Skarn",
                    "Mineralisation formed where intrusive rocks contact carbonate (limestone) host rocks. Can host gold, copper, tungsten, iron.",
                  ],
                  [
                    "Alteration",
                    "Chemical changes in rock around mineralisation. Specific alteration types (silicification, sericite, propylitic, potassic) are diagnostic of deposit type and proximity.",
                  ],
                  [
                    "Strike",
                    "Compass direction of a mineralised body at the surface. &quot;Strike length&quot; is how far the body extends along that direction.",
                  ],
                  [
                    "Dip",
                    "Angle a mineralised body makes with horizontal. A vertical vein has a 90° dip; a horizontal layer has a 0° dip.",
                  ],
                  [
                    "Pinch and swell",
                    "Mineralised body that thickens and thins along strike. Common in shear-zone gold and can complicate resource estimation.",
                  ],
                  [
                    "Cut-off grade",
                    "Minimum grade at which rock is counted as ore. Lower cut-offs increase tonnes but reduce average grade. See the NI 43-101 guide for how this affects resource numbers.",
                  ],
                  [
                    "Recovery",
                    "Percentage of metal that can be extracted from ore during processing. Free-milling gold can hit 95%+; refractory ore may drop to 70-80%.",
                  ],
                ].map(([term, def]) => (
                  <div
                    key={term}
                    className="bg-slate-800/50 border border-slate-700 rounded-lg p-4"
                  >
                    <h4 className="text-base font-bold text-gold-400 mb-1">
                      {term}
                    </h4>
                    <p
                      className="text-slate-300 text-sm mb-0"
                      dangerouslySetInnerHTML={{ __html: def }}
                    />
                  </div>
                ))}
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                For deeper definitions of these and related terms, see the{" "}
                <Link
                  href="/glossary"
                  className="text-gold-400 hover:underline"
                >
                  Mining Glossary
                </Link>
                .
              </p>
            </section>

            {/* Section 9 — Press Release Tricks */}
            <section id="press-release-tricks" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The press-release tricks to watch for
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                None of these is fraud — they are all technically compliant
                disclosure. They are techniques used by IR teams to present
                ordinary results favourably. Spotting them is most of what
                separates informed retail investors from the rest.
              </p>
              {[
                {
                  n: 1,
                  title: "Composite intervals with internal dilution",
                  body: "A headline like '50m at 2 g/t Au' may be composed of 10m at 8 g/t plus 40m at 0.5 g/t. The composite average is technically correct but masks a narrow high-grade vein in mostly-waste rock. Always look for an internal breakdown or a 'including' sub-interval that tells you where the grade actually sits.",
                },
                {
                  n: 2,
                  title: "Down-hole width without true width",
                  body: "If a release reports widths without specifying true width, default to assuming down-hole. For steeply-dipping bodies drilled at typical angles, real-world thickness is often 60-80% of the reported number.",
                },
                {
                  n: 3,
                  title: "Cherry-picked holes",
                  body: "A press release titled 'positive drill results' that only details 2-3 of 10 holes drilled is selecting the best. Other holes from the same program either hit lower grades or missed. Check the SEDAR+ filing or the drill location map for the complete picture.",
                },
                {
                  n: 4,
                  title: "Aggressive gold-equivalent calculations",
                  body: "Poly-metallic deposits use gold-equivalent (AuEq) to combine multiple metals into one headline grade. AuEq depends on assumed metal prices and recoveries. A 3 g/t AuEq calculated at $2,400 gold and $35 silver looks worse at $2,100 gold and $27 silver. Always check the assumptions footnote.",
                },
                {
                  n: 5,
                  title: "ppb instead of g/t",
                  body: "An early-stage company reporting '600 ppb gold from a surface sample' is reporting 0.6 g/t — below most economic thresholds. ppb in soil or rock chip work is normal and useful for vectoring, but ppb-based hype in a stock-promotion context is a red flag.",
                },
                {
                  n: 6,
                  title: "Inverted depth-to-target language",
                  body: "Phrases like 'mineralisation extends to depth' or 'open in all directions' sound positive but can be filler when no actual new intercepts have been added. If a release uses this language without specific new step-out hits, the company is signalling activity without progress.",
                },
                {
                  n: 7,
                  title: "Historical data dressed as new news",
                  body: "Some releases describe previously-published intercepts or historical drilling from prior operators as if they were new. Read carefully — anything described as 'previously reported,' 'historical,' or 'from prior operator' is old news.",
                },
                {
                  n: 8,
                  title: "Visual estimates ahead of assays",
                  body: "Pre-assay visual estimates ('visible gold logged') can move stocks but are not confirmed grades. Geologists can see gold flecks in core but cannot tell concentration without an assay. Some visible-gold intercepts assay below 1 g/t; others come in at 100+. Wait for assays.",
                },
                {
                  n: 9,
                  title: "Promotional headline grades from short intervals",
                  body: "A 0.5m intercept at 40 g/t is technically a high-grade hit but contributes 20 gram-metres — less than a 50m intercept at 1 g/t. Short-interval bonanza headlines should be read in gram-metre terms before assigning weight.",
                },
                {
                  n: 10,
                  title: "Delayed disclosure of disappointing programs",
                  body: "A successful program produces a string of release dates. A drill program that completed two months ago with no further releases is statistically more likely to have produced disappointing results than expected. The absence of news is its own news.",
                },
              ].map((trick) => (
                <div
                  key={trick.n}
                  className="mb-5 bg-slate-800/50 border border-slate-700 rounded-lg p-5"
                >
                  <h4 className="text-lg font-bold text-red-300 mb-2">
                    {trick.n}. {trick.title}
                  </h4>
                  <p className="text-slate-300 mb-0 text-sm leading-relaxed">
                    {trick.body}
                  </p>
                </div>
              ))}
            </section>

            {/* Section 10 — Worked Example */}
            <section id="worked-example" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Worked example — translating a real drill table
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Here is the kind of drill table you will see in the body of a
                press release. The headline read &quot;multiple high-grade
                intercepts including 24.0m at 3.85 g/t Au.&quot;
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Hole
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        From (m)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        To (m)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Width (m)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Au (g/t)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        g·m
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        AB-26-01
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        128.4
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        152.4
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        24.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        3.85
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        92.4
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 text-xs italic">
                        incl.
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        141.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        145.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">4.5</td>
                      <td className="border border-slate-700 px-3 py-2">
                        18.2
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        81.9
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        AB-26-02
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        85.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        102.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        17.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.42
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        24.1
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        AB-26-03
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        210.5
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        214.0
                      </td>
                      <td className="border border-slate-700 px-3 py-2">3.5</td>
                      <td className="border border-slate-700 px-3 py-2">
                        12.4
                      </td>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        43.4
                      </td>
                    </tr>
                  </tbody>
                </table>
                <p className="text-xs text-slate-500 italic mt-1">
                  All widths down-hole. True width estimated to be 70-80% of
                  intercept length. Composite grades weighted by interval.
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Translation, hole by hole:
              </p>
              <ul className="list-disc pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    AB-26-01 headline (24m at 3.85 g/t = 92.4 g·m)
                  </strong>{" "}
                  is a strong intercept by any measure. But check the included
                  4.5m at 18.2 g/t — it accounts for 81.9 g·m out of the 92.4
                  total. That means the other 19.5m of the intercept averages
                  about 0.54 g/t — below the open-pit economic floor. The
                  &quot;24m at 3.85 g/t&quot; is technically correct but mostly
                  represents a narrow high-grade vein within a much wider zone
                  of waste rock. The deposit needs underground mining at the
                  4.5m vein, not bulk open-pit at the 24m envelope.
                </li>
                <li>
                  <strong className="text-gold-400">
                    AB-26-02 (17m at 1.42 g/t = 24.1 g·m)
                  </strong>{" "}
                  is a moderate result. Reasonable open-pit grade over usable
                  width. Not a discovery, but a useful zone-confirming intercept
                  if it is within the modeled envelope. About a quarter of the
                  value of AB-26-01 on a gram-metre basis.
                </li>
                <li>
                  <strong className="text-gold-400">
                    AB-26-03 (3.5m at 12.4 g/t = 43.4 g·m)
                  </strong>{" "}
                  is half of AB-26-01&apos;s value but with no internal
                  dilution. It is high-grade and clean. The narrower width
                  limits mining method options but the grade is excellent.
                </li>
                <li>
                  <strong>True width.</strong> Applying the disclosed 70-80%
                  factor: AB-26-01&apos;s 24m becomes about 18m true width. The
                  4.5m internal high-grade becomes about 3.4m. Still meaningful,
                  but the down-hole headline is rosier than reality.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The headline reading the release as &quot;24m at 3.85 g/t
                Au&quot; is technically accurate but conceals that the deposit
                shape on display is a narrow high-grade vein with sub-economic
                wallrock — a meaningfully different mining proposition than what
                the headline implies. This is normal disclosure, not fraud. It
                is also why reading the body of the release matters more than
                the title.
              </p>
            </section>

            {/* Tools */}
            <section id="tools" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Tools to speed this up
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Tracking drill results manually across the 500+ companies in the
                junior mining universe is impractical. The tools below automate
                the work:
              </p>
              <div className="grid md:grid-cols-2 gap-4 my-6">
                <Link
                  href="/investor-tools/drill-scanner"
                  className="block bg-slate-800 border border-gold-500/40 hover:border-gold-500 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Drill Scanner →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Scans recent drill press releases across the database.
                    Filter by grade-times-width, by metal, and by company. Finds
                    the real catalysts under the noise.
                  </p>
                </Link>
                <Link
                  href="/investor-tools/grade-ranker"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Grade Ranker →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Compare resource grades across 500+ companies. Filter for
                    deposits in your preferred grade tier — sub-economic
                    surprises don&apos;t make the list.
                  </p>
                </Link>
                <Link
                  href="/investor-tools/ni43-101-analyzer"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    NI 43-101 Analyzer →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    AI-assisted extraction of resource tables and economic
                    summaries from any uploaded technical report.
                  </p>
                </Link>
                <Link
                  href="/companies"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Company Database →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Browse 500+ junior miners. Each company page lists recent
                    news releases including drill announcements.
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
                    href="/guides/junior-gold-mining-companies-guide"
                    className="text-gold-400 hover:underline"
                  >
                    The Complete Guide to Junior Gold Mining Companies →
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
