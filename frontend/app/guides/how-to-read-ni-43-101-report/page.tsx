import type { Metadata } from "next";
import Link from "next/link";

const CANONICAL =
  "https://juniorminingintelligence.com/guides/how-to-read-ni-43-101-report";

export const metadata: Metadata = {
  title: "How to Read an NI 43-101 Report: A Plain-English Guide for Investors",
  description:
    "Step-by-step guide to reading an NI 43-101 technical report. Learn which sections to skim, which to read, what resource categories mean, and 10 red flags that signal a weak report.",
  keywords: [
    "how to read NI 43-101",
    "NI 43-101 explained",
    "NI 43-101 sections",
    "qualified person mining",
    "mineral resource categories",
    "indicated vs inferred resources",
    "technical report mining",
    "NI 43-101 red flags",
    "PEA PFS DFS explained",
    "mineral reserve mineral resource",
  ],
  openGraph: {
    title: "How to Read an NI 43-101 Report: A Plain-English Guide",
    description:
      "Skip the 300 pages of jargon. Learn the 5 sections that actually matter, what resource categories mean, and 10 red flags that signal a weak report.",
    type: "article",
    url: CANONICAL,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "How to Read an NI 43-101 Technical Report",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "How to Read an NI 43-101 Report — Plain English Guide",
    description:
      "Skip the 300-page wall of jargon. The 5 sections that matter and 10 red flags to spot a weak report.",
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
    "How to Read an NI 43-101 Report: A Plain-English Guide for Investors",
  description:
    "Step-by-step guide to reading an NI 43-101 technical report — which sections matter, what resource categories mean, and the red flags that signal a weak report.",
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
    { "@type": "DefinedTerm", name: "NI 43-101" },
    { "@type": "Thing", name: "Mineral Resource Estimate" },
    { "@type": "Thing", name: "Qualified Person" },
  ],
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is NI 43-101?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "NI 43-101 is the Canadian National Instrument that governs how mining companies listed on Canadian exchanges (TSX, TSXV, CSE) disclose scientific and technical information about mineral projects. Every public disclosure of a mineral resource, reserve, or economic study must be prepared or supervised by a Qualified Person and follow the NI 43-101 standards. It is the most widely-used mineral reporting standard in the world.",
      },
    },
    {
      "@type": "Question",
      name: "How long is a typical NI 43-101 report?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "An NI 43-101 technical report is typically 150 to 400 pages long. Resource-stage reports tend to be shorter (150-250 pages), while feasibility-stage reports (PFS, DFS) often exceed 400 pages because they include detailed engineering, economic modelling, environmental assessment, and capital cost estimates. You do not need to read the whole document — most investors should focus on Items 14, 15, 16, 22, and the Summary.",
      },
    },
    {
      "@type": "Question",
      name: "What is the difference between Inferred, Indicated, and Measured resources?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "These are the three resource confidence categories in NI 43-101. Inferred Resources have the lowest geological confidence — they are based on limited drilling and cannot be used in an economic study. Indicated Resources have moderate confidence with enough drill density to support preliminary economic modelling and can be converted to Probable Reserves. Measured Resources have the highest confidence and can be converted to Proven Reserves. The category mix matters enormously: a deposit that is 90% Inferred is far less proven than one that is 60% Measured + Indicated.",
      },
    },
    {
      "@type": "Question",
      name: "Who is a Qualified Person?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A Qualified Person (QP) is an individual professional geologist or mining engineer with at least five years of relevant experience and membership in a recognised professional association (such as PEng, PGeo, AusIMM, or SME). NI 43-101 requires that every technical report — and every public statement about mineral resources — be prepared or supervised by a QP. The QP signs the report and is personally responsible for the technical content. Independent QPs (not employed by the company) carry more weight than internal ones.",
      },
    },
    {
      "@type": "Question",
      name: "Are Inferred Resources reliable enough to invest on?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Inferred Resources should be treated as a hypothesis, not a proof. NI 43-101 explicitly prohibits using Inferred Resources in PEAs without a heavy disclaimer, and they cannot be used in PFS or DFS economic studies at all. Historically, a meaningful fraction of Inferred ounces never convert to Indicated or Measured after infill drilling. If the entire investment case rests on Inferred Resources, you are betting that future drilling confirms what limited drilling suggested — sometimes it does, sometimes it does not.",
      },
    },
    {
      "@type": "Question",
      name: "What does PEA vs PFS vs DFS mean?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "These are the three levels of economic study under NI 43-101, in increasing order of rigour. A PEA (Preliminary Economic Assessment) is a scoping study with accuracy of about plus-or-minus 30%, can use Inferred Resources, and is the cheapest to produce. A PFS (Pre-Feasibility Study) requires Indicated or Measured Resources, has plus-or-minus 20-25% accuracy, and demonstrates economic viability. A DFS (Definitive Feasibility Study, sometimes called Feasibility Study) is the bankable study with plus-or-minus 10-15% accuracy, full engineering, and is what financiers require before construction. Moving from PEA to DFS typically takes 2-5 years and costs $5M-$50M+.",
      },
    },
    {
      "@type": "Question",
      name: "Can companies fake or inflate NI 43-101 numbers?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Outright fabrication is rare and career-ending for the Qualified Person involved (see the Bre-X scandal that drove the creation of NI 43-101 in the first place). However, legal numerical optimism happens frequently: aggressive cut-off grades, generous metal price assumptions, optimistic recovery rates, or selectively-reported drill intervals. Recognising these requires checking the assumptions section. We cover the most common tricks in the Red Flags section below.",
      },
    },
    {
      "@type": "Question",
      name: "Where can I find a company's NI 43-101 reports?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "All NI 43-101 reports for Canadian-listed companies must be filed on SEDAR+ (sedarplus.ca), the Canadian regulator's filing system. Search for the company, then look under 'Reports — Technical' or 'Mineral Project Disclosure.' Many companies also link to their reports directly from their investor-relations pages. Junior Mining Intelligence aggregates NI 43-101 reports for the 500+ companies in its database — they appear on each company's detail page under Documents.",
      },
    },
    {
      "@type": "Question",
      name: "Do I need to read the whole technical report?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "No. Reading a 300-page NI 43-101 cover-to-cover is rarely worth the time for a retail investor. Most of the document is methodology, certifications, and supporting data the regulator requires. The five sections that contain almost all the investment-relevant information are Item 1 (Summary), Item 14 (Resource Estimate), Item 15 (Reserve Estimate, if applicable), Item 16 (Mining Methods), and Item 22 (Economic Analysis). With practice you can extract the key signals from a report in 15-30 minutes.",
      },
    },
    {
      "@type": "Question",
      name: "What is a cut-off grade and why does it matter?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Cut-off grade is the minimum mineral grade at which a tonne of rock is included in the resource estimate. A lower cut-off grade increases reported tonnes and ounces but reduces the average grade. Companies sometimes report resources at multiple cut-offs — pay attention to which cut-off they use in headline marketing versus what the economic study actually assumes. A 0.5 g/t cut-off may make a resource look impressive on a press release but may not be economic to mine at current gold prices.",
      },
    },
  ],
};

const howToSchema = {
  "@context": "https://schema.org",
  "@type": "HowTo",
  name: "How to Read an NI 43-101 Technical Report in 30 Minutes",
  description:
    "A focused workflow for extracting the investment-relevant information from an NI 43-101 technical report.",
  totalTime: "PT30M",
  step: [
    {
      "@type": "HowToStep",
      name: "Read the Summary (Item 1)",
      text: "Item 1 is a 5-15 page executive summary written by the Qualified Person. It contains the headline resource numbers, the economic results, and the QP's conclusions. Read this first.",
    },
    {
      "@type": "HowToStep",
      name: "Check the Resource Estimate (Item 14)",
      text: "Item 14 contains the resource table broken down by category (Inferred, Indicated, Measured). Note the tonnes, grade, and contained metal. Critically, note the cut-off grade used.",
    },
    {
      "@type": "HowToStep",
      name: "Check Reserves (Item 15, if applicable)",
      text: "Reserves only exist if the project has progressed to PFS or DFS. Reserves are the portion of Indicated + Measured Resources that economic studies have shown can be profitably mined.",
    },
    {
      "@type": "HowToStep",
      name: "Skim Mining Methods (Item 16)",
      text: "Open-pit vs underground, mining rate, strip ratio. These drive capital and operating costs.",
    },
    {
      "@type": "HowToStep",
      name: "Read Economic Analysis (Item 22)",
      text: "NPV, IRR, payback period, AISC, and — most importantly — the metal price and discount rate assumptions used. Stress-test the result against today's metal price.",
    },
    {
      "@type": "HowToStep",
      name: "Check Risks and Uncertainties (Item 25)",
      text: "The QP must disclose material risks. Read this — it is often where you find acknowledged weaknesses the marketing materials skip.",
    },
  ],
};

export default function HowToReadNI43101Guide() {
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
                <li className="text-slate-300">
                  How to Read an NI 43-101 Report
                </li>
              </ol>
            </nav>

            <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              How to Read an NI 43-101 Report
            </h1>
            <p className="text-xl text-slate-300 mb-4">
              A plain-English guide to skimming a 300-page technical report and
              extracting the five things that actually matter to investors.
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <span>Updated: May 28, 2026</span>
              <span>20 min read</span>
              <span>5,200 words</span>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 30-second answer (AI Overview bait) */}
          <div className="bg-gradient-to-br from-gold-500/10 to-gold-500/5 border border-gold-500/30 rounded-lg p-6 mb-12">
            <h2 className="text-lg font-bold text-gold-400 mb-3">
              The 30-second answer
            </h2>
            <p className="text-slate-200 mb-3">
              An NI 43-101 technical report is the Canadian regulatory standard
              for disclosing mineral resources. To read one quickly:
            </p>
            <ol className="list-decimal pl-6 space-y-1 text-slate-200">
              <li>
                Read <strong className="text-gold-400">Item 1 (Summary)</strong>{" "}
                — everything that matters in 10 pages.
              </li>
              <li>
                Open{" "}
                <strong className="text-gold-400">
                  Item 14 (Resource Estimate)
                </strong>{" "}
                — note tonnes, grade, contained metal, and cut-off grade by
                category.
              </li>
              <li>
                If reserves exist, check{" "}
                <strong className="text-gold-400">Item 15</strong>.
              </li>
              <li>
                Read{" "}
                <strong className="text-gold-400">
                  Item 22 (Economic Analysis)
                </strong>{" "}
                — NPV, IRR, AISC, and the metal-price assumption used.
              </li>
              <li>
                Check{" "}
                <strong className="text-gold-400">
                  Item 25 (Risks and Uncertainties)
                </strong>{" "}
                — where the QP discloses what marketing materials skip.
              </li>
            </ol>
            <p className="text-slate-300 mt-3 mb-0 text-sm">
              You can extract the investment thesis from most reports in 30
              minutes. The other 270+ pages are methodology and supporting data.
            </p>
          </div>

          {/* TOC */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-12">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Table of Contents
            </h2>
            <ol className="space-y-2 text-slate-300 list-decimal pl-6">
              <li>
                <a href="#what-is" className="hover:text-gold-400">
                  What NI 43-101 is and why it exists
                </a>
              </li>
              <li>
                <a href="#structure" className="hover:text-gold-400">
                  The 27-item structure (overview)
                </a>
              </li>
              <li>
                <a href="#five-sections" className="hover:text-gold-400">
                  The five sections that matter
                </a>
              </li>
              <li>
                <a href="#resource-categories" className="hover:text-gold-400">
                  Resource categories explained: Inferred, Indicated, Measured
                </a>
              </li>
              <li>
                <a
                  href="#reserves-vs-resources"
                  className="hover:text-gold-400"
                >
                  Reserves vs Resources — the distinction that matters
                </a>
              </li>
              <li>
                <a href="#pea-pfs-dfs" className="hover:text-gold-400">
                  PEA vs PFS vs DFS — the economic study hierarchy
                </a>
              </li>
              <li>
                <a href="#qualified-person" className="hover:text-gold-400">
                  The Qualified Person — who they are and why it matters
                </a>
              </li>
              <li>
                <a href="#red-flags" className="hover:text-gold-400">
                  10 red flags that signal a weak report
                </a>
              </li>
              <li>
                <a href="#worked-example" className="hover:text-gold-400">
                  Worked example — translating a real resource table
                </a>
              </li>
              <li>
                <a href="#common-mistakes" className="hover:text-gold-400">
                  Common mistakes retail investors make
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
            {/* Section 1 — What is NI 43-101 */}
            <section id="what-is" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                What NI 43-101 is and why it exists
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                <strong className="text-gold-400">NI 43-101</strong> (National
                Instrument 43-101) is the Canadian regulatory standard for the
                public disclosure of scientific and technical information about
                mineral projects. It governs how companies listed on the{" "}
                <strong className="text-gold-400">TSX</strong>,{" "}
                <strong className="text-gold-400">TSX Venture Exchange</strong>,
                and <strong className="text-gold-400">CSE</strong> talk about
                mineral resources, reserves, and economic studies — what they
                must disclose, who must sign off, and how the numbers must be
                calculated.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                NI 43-101 came into force in 2001 in direct response to the{" "}
                <strong className="text-gold-400">Bre-X scandal</strong>. In
                1997, Bre-X Minerals collapsed after its much-hyped Busang gold
                deposit in Indonesia turned out to be a salting fraud — the
                drill core had been doctored with shavings of placer gold.
                Investors lost about $6 billion. Canadian regulators spent the
                next four years building a standard that would make a
                Bre-X-scale fraud structurally harder to commit, and the result
                is the document any junior-mining investor today still has to
                wrestle with.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The core idea is simple: every public statement about a mineral
                resource must be backed by a written technical report, prepared
                or supervised by a credentialed{" "}
                <strong className="text-gold-400">Qualified Person</strong> who
                puts their professional license on the line, and filed with the
                regulator where any investor can read it. The reports follow a
                strict template of 27 numbered items so that data is comparable
                across companies and projects.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                NI 43-101 is the most widely-recognised mineral reporting
                standard in the world. Comparable standards exist elsewhere —
                the <strong className="text-gold-400">JORC Code</strong> in
                Australia, the{" "}
                <strong className="text-gold-400">SAMREC Code</strong> in South
                Africa, and the SK-1300 standard for US-listed issuers — and all
                four are broadly aligned through the CRIRSCO international
                standards body. If you can read an NI 43-101, you can read any
                of them.
              </p>
              <div className="bg-slate-800 border-l-4 border-gold-500 p-6 my-6">
                <h3 className="text-lg font-bold text-gold-400 mb-2">
                  Key takeaway
                </h3>
                <p className="text-slate-300 mb-0">
                  NI 43-101 doesn&apos;t guarantee a project is a good
                  investment. It guarantees that the technical claims have been
                  signed by a professional whose career depends on them being
                  defensible. Your job as an investor is to read what the QP
                  actually said — not what the marketing deck claims they said.
                </p>
              </div>
            </section>

            {/* Section 2 — Structure */}
            <section id="structure" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The 27-item structure
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Every NI 43-101 technical report follows the same numbered table
                of contents. Here is the full list with a one-line note on what
                each item contains and how much attention it deserves from a
                typical investor.
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400 w-12">
                        #
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Item
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        What it contains
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Read?
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      [
                        "1",
                        "Summary",
                        "Executive summary by the QP",
                        "Yes — first",
                      ],
                      [
                        "2",
                        "Introduction",
                        "Scope, terms of reference",
                        "Skim",
                      ],
                      [
                        "3",
                        "Reliance on Other Experts",
                        "Where QP relied on outside reports",
                        "Skim",
                      ],
                      [
                        "4",
                        "Property Description",
                        "Location, ownership, titles",
                        "Skim",
                      ],
                      [
                        "5",
                        "Accessibility, Climate, Infrastructure",
                        "Logistics",
                        "Skim",
                      ],
                      ["6", "History", "Prior owners and drilling", "Skim"],
                      [
                        "7",
                        "Geological Setting",
                        "Regional and local geology",
                        "Skip unless geologist",
                      ],
                      [
                        "8",
                        "Deposit Types",
                        "Style of mineralization",
                        "Skip unless geologist",
                      ],
                      ["9", "Exploration", "Surveys and surface work", "Skim"],
                      [
                        "10",
                        "Drilling",
                        "Total metres, programmes",
                        "Yes — note recency and density",
                      ],
                      [
                        "11",
                        "Sample Preparation",
                        "Assay lab protocols",
                        "Skip",
                      ],
                      [
                        "12",
                        "Data Verification",
                        "QP&apos;s independent checks",
                        "Yes — short but critical",
                      ],
                      [
                        "13",
                        "Mineral Processing",
                        "Metallurgy and recovery",
                        "Yes if economic study attached",
                      ],
                      [
                        "14",
                        "Mineral Resource Estimate",
                        "THE resource table",
                        "Yes — most important",
                      ],
                      [
                        "15",
                        "Mineral Reserve Estimate",
                        "Reserves (PFS/DFS only)",
                        "Yes if present",
                      ],
                      [
                        "16",
                        "Mining Methods",
                        "Open-pit / underground",
                        "Yes — drives cost",
                      ],
                      [
                        "17",
                        "Recovery Methods",
                        "Mill / leach / flotation",
                        "Yes if economic study",
                      ],
                      [
                        "18",
                        "Project Infrastructure",
                        "Power, water, roads",
                        "Skim",
                      ],
                      [
                        "19",
                        "Market Studies",
                        "Metal price assumptions",
                        "Yes — check the price",
                      ],
                      [
                        "20",
                        "Environmental, Permitting, Social",
                        "Risks",
                        "Yes — jurisdictional risk",
                      ],
                      [
                        "21",
                        "Capital and Operating Costs",
                        "CAPEX and OPEX",
                        "Yes if economic study",
                      ],
                      [
                        "22",
                        "Economic Analysis",
                        "NPV, IRR, payback, AISC",
                        "Yes — second-most important",
                      ],
                      [
                        "23",
                        "Adjacent Properties",
                        "Nearby projects (cannot be used in own resource)",
                        "Skim",
                      ],
                      [
                        "24",
                        "Other Relevant Data",
                        "Whatever didn&apos;t fit elsewhere",
                        "Skim",
                      ],
                      [
                        "25",
                        "Interpretation and Conclusions",
                        "QP&apos;s honest assessment",
                        "Yes — often candid",
                      ],
                      [
                        "26",
                        "Recommendations",
                        "Next-stage work plan",
                        "Yes — what is the company planning?",
                      ],
                      ["27", "References", "Bibliography", "Skip"],
                    ].map(([num, item, contents, read], i) => (
                      <tr
                        key={i}
                        className={i % 2 === 0 ? "" : "bg-slate-800/50"}
                      >
                        <td className="border border-slate-700 px-3 py-2 font-mono">
                          {num}
                        </td>
                        <td
                          className="border border-slate-700 px-3 py-2 font-semibold"
                          dangerouslySetInnerHTML={{ __html: item }}
                        />
                        <td
                          className="border border-slate-700 px-3 py-2"
                          dangerouslySetInnerHTML={{ __html: contents }}
                        />
                        <td className="border border-slate-700 px-3 py-2 text-slate-400">
                          {read}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The investment-relevant signal is concentrated in Items 1, 14,
                15, 16, 19, 22, and 25. A disciplined reader can extract a
                first-pass investment view from any NI 43-101 in 20 to 30
                minutes by working through that list in order.
              </p>
            </section>

            {/* Section 3 — Five sections */}
            <section id="five-sections" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The five sections that actually matter
              </h2>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 1 — Summary
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Item 1 is a 5- to 15-page executive summary written by the
                Qualified Person. It compresses the entire 300-page document
                into the key conclusions: headline resource numbers, headline
                economics, and the QP&apos;s overall view of the project.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Read this first. Always. Even before opening the press release
                the company put out about the report. Two reasons. First, the
                summary is written by the QP, not by the IR team — the tone is
                generally more measured than the marketing materials. Second, if
                there is a material difference between what the press release
                says and what the summary says, you want to spot it early. That
                gap is almost always informative.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 14 — Mineral Resource Estimate
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The resource table is the heart of the report. It will look
                something like this:
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
                        Contained Oz (Au)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Measured
                      </td>
                      <td className="border border-slate-700 px-3 py-2">2.1</td>
                      <td className="border border-slate-700 px-3 py-2">2.4</td>
                      <td className="border border-slate-700 px-3 py-2">
                        162,000
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Indicated
                      </td>
                      <td className="border border-slate-700 px-3 py-2">8.3</td>
                      <td className="border border-slate-700 px-3 py-2">1.8</td>
                      <td className="border border-slate-700 px-3 py-2">
                        480,000
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        M+I
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        10.4
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.92
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        642,000
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        Inferred
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        14.7
                      </td>
                      <td className="border border-slate-700 px-3 py-2">1.5</td>
                      <td className="border border-slate-700 px-3 py-2">
                        709,000
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Three things to extract before moving on:
              </p>
              <ol className="list-decimal pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">The category mix.</strong>{" "}
                  In the table above, the deposit is 52% Inferred by ounces.
                  That is a meaningfully less proven resource than one that is
                  52% Measured + Indicated. (See{" "}
                  <a
                    href="#resource-categories"
                    className="text-gold-400 hover:underline"
                  >
                    Resource categories
                  </a>{" "}
                  below.)
                </li>
                <li>
                  <strong className="text-gold-400">The cut-off grade.</strong>{" "}
                  Always disclosed beneath the table. A 0.5 g/t cut-off produces
                  dramatically more tonnes than a 1.0 g/t cut-off. Check that
                  the cut-off used is realistic for the proposed mining method
                  (open-pit cut-offs are lower than underground).
                </li>
                <li>
                  <strong className="text-gold-400">The effective date.</strong>{" "}
                  The resource is a snapshot. If the report is two years old and
                  there has been infill drilling since, the actual resource may
                  have grown or shrunk meaningfully.
                </li>
              </ol>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 15 — Mineral Reserve Estimate
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Reserves only exist if the project has progressed to a PFS or
                DFS. If you are reading a resource-stage or PEA report, this
                section will say &quot;not applicable&quot; — that is normal. If
                reserves are present, they represent the portion of the
                Indicated + Measured Resource that an economic study has shown
                can be profitably mined. Reserves are categorised as{" "}
                <strong className="text-gold-400">Probable</strong> (derived
                from Indicated) or{" "}
                <strong className="text-gold-400">Proven</strong> (derived from
                Measured).
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The ratio of Reserves to Resources is informative. A high
                conversion ratio (say, 80%+) suggests a robust deposit. A low
                ratio means a meaningful portion of the resource was deemed
                uneconomic even at the report&apos;s assumed metal prices.
              </p>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 16 — Mining Methods
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The mining method drives both capital and operating cost. The
                four things to extract:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Open-pit vs underground.
                  </strong>{" "}
                  Open-pit is generally cheaper per tonne, but requires
                  shallower mineralization and tolerates lower grades.
                  Underground costs 2–4x more per tonne and demands higher grade
                  to be economic.
                </li>
                <li>
                  <strong className="text-gold-400">Strip ratio</strong>{" "}
                  (open-pit only). The number of tonnes of waste rock that must
                  be moved to access one tonne of ore. Strip ratios over 5:1
                  start to hurt economics; over 10:1 is a red flag unless grades
                  are exceptional.
                </li>
                <li>
                  <strong className="text-gold-400">Mining rate.</strong> Tonnes
                  per day or tonnes per year. Bigger is more capital but more
                  output.
                </li>
                <li>
                  <strong className="text-gold-400">Mine life.</strong> How many
                  years of mining at the planned rate. Short mine lives (under 7
                  years) often produce weak economics regardless of grade.
                </li>
              </ul>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 22 — Economic Analysis
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                This is where the QP translates everything into dollars. The
                headline numbers are:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">NPV</strong> (Net Present
                  Value, usually NPV<sub>5%</sub>): the present value of
                  projected free cash flows, discounted at 5%. A positive NPV
                  means the project is theoretically profitable at the assumed
                  metal price; a NPV many multiples of the company&apos;s market
                  cap is what makes a deposit interesting.
                </li>
                <li>
                  <strong className="text-gold-400">IRR</strong> (Internal Rate
                  of Return): the discount rate at which NPV = 0. Gold projects
                  generally need an IRR above 20% pre-tax to attract financing.
                </li>
                <li>
                  <strong className="text-gold-400">Payback period</strong>:
                  years until cumulative cash flow turns positive after start of
                  production. Sub-4 years is strong.
                </li>
                <li>
                  <strong className="text-gold-400">AISC</strong> (All-In
                  Sustaining Cost): the total cost per ounce produced including
                  sustaining capital. AISC well under the current gold price
                  gives margin for downturns. AISC near or above current price
                  means a marginal project.
                </li>
                <li>
                  <strong className="text-gold-400">Initial CAPEX</strong>: the
                  upfront capital required to build the mine. For a junior miner
                  with $30M market cap, a $400M CAPEX project will require
                  massive dilution or a take-out by a larger company.
                </li>
              </ul>
              <div className="bg-red-900/20 border-l-4 border-red-500 p-6 my-6">
                <h4 className="text-lg font-bold text-red-300 mb-2">
                  The most important number on this page
                </h4>
                <p className="text-slate-300 mb-0">
                  Find the assumed metal price. It will be buried in the
                  &quot;Key Assumptions&quot; subsection. If the report assumes
                  $2,400/oz gold and gold is currently $2,100/oz, the headline
                  NPV and IRR are higher than reality. Always mentally re-run
                  the economics at today&apos;s spot price.
                </p>
              </div>

              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Item 25 — Interpretation and Conclusions
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                This is the QP&apos;s honest assessment. In good reports it is
                where weaknesses are flagged — geological uncertainties,
                metallurgical risks, infrastructure gaps, permitting hurdles. In
                weak reports it is a bland summary that adds nothing. The
                quality of Item 25 is a tell about the quality of the entire
                report.
              </p>
            </section>

            {/* Section 4 — Resource Categories */}
            <section id="resource-categories" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Resource categories: Inferred, Indicated, Measured
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The three categories represent increasing confidence based on
                drill-hole density. NI 43-101 (and the CIM Definition Standards
                it adopts) defines them as follows.
              </p>

              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
                  <h3 className="text-xl font-bold text-slate-300 mb-2">
                    Inferred
                  </h3>
                  <p className="text-sm text-slate-400 mb-3">
                    Lowest confidence
                  </p>
                  <p className="text-slate-300 text-sm">
                    Limited drilling. Geology and grade estimated from sparse
                    data. May or may not exist as represented after infill
                    drilling. <strong className="text-red-400">Cannot</strong>{" "}
                    be used in PFS or DFS economic studies.
                  </p>
                </div>
                <div className="bg-slate-800 border border-gold-500/30 rounded-lg p-5">
                  <h3 className="text-xl font-bold text-gold-400 mb-2">
                    Indicated
                  </h3>
                  <p className="text-sm text-slate-400 mb-3">
                    Moderate confidence
                  </p>
                  <p className="text-slate-300 text-sm">
                    Drill spacing tight enough to support preliminary mine
                    planning. Can be converted to{" "}
                    <strong className="text-gold-400">Probable Reserves</strong>{" "}
                    after economic study. Eligible for PFS and DFS.
                  </p>
                </div>
                <div className="bg-slate-800 border border-emerald-500/30 rounded-lg p-5">
                  <h3 className="text-xl font-bold text-emerald-300 mb-2">
                    Measured
                  </h3>
                  <p className="text-sm text-slate-400 mb-3">
                    Highest confidence
                  </p>
                  <p className="text-slate-300 text-sm">
                    Dense drilling. Geology and grade are well-understood. Can
                    be converted to{" "}
                    <strong className="text-emerald-300">
                      Proven Reserves
                    </strong>
                    . The closest a mineral resource gets to a sure thing on
                    paper.
                  </p>
                </div>
              </div>

              <p className="text-slate-300 mb-4 leading-relaxed">
                Three things investors routinely get wrong about these
                categories:
              </p>
              <ol className="list-decimal pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong className="text-gold-400">
                    Inferred is not &quot;almost Indicated.&quot;
                  </strong>{" "}
                  The drill-spacing gap between the two is large. Industry
                  studies of conversion rates show that a meaningful fraction of
                  Inferred ounces never convert even after years of infill
                  drilling — sometimes 30% or more is reclassified downward or
                  removed entirely.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Inferred + Indicated + Measured does NOT mean &quot;total
                    resource.&quot;
                  </strong>{" "}
                  Inferred is always reported separately. The proper
                  &quot;global resource&quot; figure is the sum, but headline
                  numbers should always be split out. Press releases that bury
                  the Inferred portion into a single big number are doing
                  marketing, not disclosure.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Resources are not Reserves.
                  </strong>{" "}
                  This is the single most common misunderstanding in junior
                  mining. A resource is a geological estimate of how much metal
                  is in the ground. A reserve is the portion of the resource
                  that an economic study has shown can be profitably mined. Many
                  resource-stage juniors have impressive resource numbers and
                  zero reserves. The conversion from one to the other is where
                  projects go to die.
                </li>
              </ol>
              <p className="text-slate-300 mb-4 leading-relaxed">
                For the definitions of these and other terms in isolation, see
                our{" "}
                <Link
                  href="/glossary"
                  className="text-gold-400 hover:underline"
                >
                  Mining Glossary
                </Link>{" "}
                — particularly the entries for{" "}
                <Link
                  href="/glossary"
                  className="text-gold-400 hover:underline"
                >
                  Indicated Resource
                </Link>
                ,{" "}
                <Link
                  href="/glossary"
                  className="text-gold-400 hover:underline"
                >
                  Inferred Resource
                </Link>
                , and{" "}
                <Link
                  href="/glossary"
                  className="text-gold-400 hover:underline"
                >
                  Mineral Reserve
                </Link>
                .
              </p>
            </section>

            {/* Section 5 — Reserves vs Resources */}
            <section id="reserves-vs-resources" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Reserves vs Resources — the distinction that matters
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                If you take one thing away from this guide, take this: a
                Resource is geology; a Reserve is economics.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A resource estimate says: based on our drilling, we believe X
                million tonnes of rock at Y grade exists in this location. That
                is a geological claim. It says nothing about whether the metal
                can be extracted at a profit. A reserve estimate says: based on
                our economic study, X million tonnes of rock at Y grade can be
                profitably mined and processed at our assumed metal prices and
                cost base. That is an engineering and financial claim.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The conversion is constrained by NI 43-101 in two directions.
                You can only convert Indicated Resources to Probable Reserves,
                and Measured Resources to Proven Reserves — Inferred Resources
                cannot be converted at all. And you can only declare reserves
                after a PFS or DFS economic study has been completed. PEAs do
                not produce reserves.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Practical implication: if a junior miner has only a resource
                estimate and no reserves, the company is fundamentally still
                betting that the deposit can be economically mined. The
                geological case is being made; the economic case is not yet
                proven. That is normal for the stage — most TSXV exploration
                companies operate this way for years — but it should change how
                you think about valuation.
              </p>
            </section>

            {/* Section 6 — PEA/PFS/DFS */}
            <section id="pea-pfs-dfs" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                PEA vs PFS vs DFS — the economic study hierarchy
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                NI 43-101 defines three levels of economic study. Each is more
                rigorous, more expensive, and more bankable than the one before.
              </p>
              <div className="overflow-x-auto mb-6">
                <table className="w-full border border-slate-700 text-slate-300 text-sm">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Study
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Accuracy
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Uses Inferred?
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Produces Reserves?
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Typical cost
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-left text-gold-400">
                        Time
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        PEA
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        ±30%
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-yellow-300">
                        Yes (with disclaimer)
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-red-400">
                        No
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        $300K–$2M
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        3–9 months
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        PFS
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        ±20–25%
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-red-400">
                        No
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-emerald-400">
                        Yes (Probable)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        $2M–$10M
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        9–18 months
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-slate-700 px-3 py-2 font-semibold">
                        DFS
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        ±10–15%
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-red-400">
                        No
                      </td>
                      <td className="border border-slate-700 px-3 py-2 text-emerald-400">
                        Yes (Proven + Probable)
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        $10M–$50M+
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        18–36 months
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The implication for valuation: a junior with a PEA is several
                years and tens of millions of dollars away from being
                financeable. A junior with a DFS is one step from construction.
                The market prices these stages very differently, and rightly so.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                One specific NI 43-101 quirk worth knowing: PEAs are allowed to
                include Inferred Resources, but only with a clear disclaimer
                that &quot;there is no certainty that the preliminary economic
                assessment will be realised.&quot; If you see that exact
                disclaimer language quoted in marketing materials, that is the
                law forcing the company to remind you that the economic case
                rests partly on geology that has not yet been proven out.
              </p>
            </section>

            {/* Section 7 — Qualified Person */}
            <section id="qualified-person" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                The Qualified Person — who they are and why it matters
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                A{" "}
                <strong className="text-gold-400">Qualified Person (QP)</strong>{" "}
                under NI 43-101 must be:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-300 mb-4">
                <li>
                  An engineer or geoscientist with{" "}
                  <strong className="text-gold-400">
                    at least 5 years of relevant experience
                  </strong>{" "}
                  in the type of project being reported on.
                </li>
                <li>
                  A member in good standing of a{" "}
                  <strong className="text-gold-400">
                    recognised professional association
                  </strong>
                  : PEng or PGeo in Canada, AusIMM in Australia, SME in the US,
                  GSL in the UK, and a list of others.
                </li>
                <li>
                  Identified by name in the report, with their certifications,
                  affiliations, and a signed Certificate of Qualified Person.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                The QP signs the report and assumes personal professional
                liability for it. A QP found to have signed materially false
                technical work can lose their license — career-ending. That is
                what gives the NI 43-101 standard its teeth.
              </p>
              <h3 className="text-2xl font-semibold text-slate-200 mb-3 mt-8">
                Independent vs internal QPs
              </h3>
              <p className="text-slate-300 mb-4 leading-relaxed">
                NI 43-101 distinguishes between independent QPs (not employees
                of, or in a financial relationship with, the issuer) and
                internal QPs. Some report types — notably PEAs, PFS, and DFS on
                material properties — must use independent QPs. Many resource
                updates can use internal QPs. All else equal, independent QPs
                are a stronger signal of credibility because their professional
                reputation is not tied to the company.
              </p>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Check the names. A QP with 30 years of experience at a major
                consultancy (SRK, AMC, RPA-Tetra Tech, Mining Plus, Wood, Knight
                Piésold) signing a report carries weight. A rarely-published
                name signing a contentious PEA at an unknown consultancy is
                worth a closer look.
              </p>
            </section>

            {/* Section 8 — Red flags */}
            <section id="red-flags" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                10 red flags that signal a weak report
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                None of these is necessarily disqualifying on its own. Two or
                three together usually are.
              </p>

              {[
                {
                  n: 1,
                  title:
                    "Headline numbers blend Inferred with Indicated + Measured",
                  body: "A press release that touts &quot;5 million ounces&quot; without splitting out how much is Inferred is doing marketing, not disclosure. Always check Item 14 for the breakdown. If 70% of the &quot;5 million&quot; is Inferred, that is a very different deposit.",
                },
                {
                  n: 2,
                  title: "Aggressive metal price assumption",
                  body: "If the gold price assumption in Item 19 is materially above current spot — say, $2,500/oz when spot is $2,100/oz — every economic number is inflated. Mentally rerun NPV and IRR at spot. If the project only works at +20% above spot, it is marginal.",
                },
                {
                  n: 3,
                  title: "Unrealistically low cut-off grade",
                  body: "A cut-off grade significantly below comparable peer projects boosts headline tonnes and ounces at the expense of average grade. If similar deposits use 0.5 g/t and this report uses 0.3 g/t, ask why.",
                },
                {
                  n: 4,
                  title:
                    "Inconsistency between the report and the press release",
                  body: "The QP-written summary in Item 1 should match the company&apos;s press release in tone and headline figures. Material differences usually mean the marketing version is selectively emphasising favourable data. Always trust the report, not the release.",
                },
                {
                  n: 5,
                  title:
                    "No independent QP on a material study (PEA, PFS, DFS)",
                  body: "NI 43-101 generally requires independent QPs for material projects. If a key economic study is signed only by internal QPs, ask why. Sometimes the answer is benign (the company has senior in-house expertise), sometimes it is not.",
                },
                {
                  n: 6,
                  title: "Capital cost (CAPEX) far exceeds company market cap",
                  body: "A junior with a $30M market cap presenting a PEA with $500M initial CAPEX is implicitly assuming massive future dilution or a take-out. Neither is wrong, but it changes what you are actually investing in.",
                },
                {
                  n: 7,
                  title: "Recovery assumptions without metallurgical test work",
                  body: "PEA-stage reports sometimes assume 90%+ metal recovery without bench-scale test work to back it. If Item 13 (Mineral Processing) does not cite metallurgical samples and recovery testing, the economic numbers rest on an assumption that may not hold.",
                },
                {
                  n: 8,
                  title: "Old effective date",
                  body: "Resource estimates have a stated effective date. Drilling continues; markets move. A report with a 3-year-old effective date may not reflect the current resource. If there has been material drilling since, the current resource may be larger or smaller.",
                },
                {
                  n: 9,
                  title:
                    "Unresolved jurisdictional or permitting risk in Item 20",
                  body: "Item 20 covers environmental, permitting, and social licence. A bland Item 20 in a frontier jurisdiction is concerning. Look for acknowledgement of specific permits required and timelines, not just generic statements that &quot;permits will be obtained.&quot;",
                },
                {
                  n: 10,
                  title: "Item 25 reads like marketing copy",
                  body: "The QP&apos;s interpretation and conclusions should be substantive. If Item 25 is two paragraphs of bland endorsement with no discussion of geological uncertainties, metallurgical risks, or open questions, the QP is either uncritical or constrained. Either way, the report is doing less for you than it should.",
                },
              ].map((flag) => (
                <div
                  key={flag.n}
                  className="mb-5 bg-slate-800/50 border border-slate-700 rounded-lg p-5"
                >
                  <h4 className="text-lg font-bold text-red-300 mb-2">
                    {flag.n}.{" "}
                    <span dangerouslySetInnerHTML={{ __html: flag.title }} />
                  </h4>
                  <p
                    className="text-slate-300 mb-0 text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: flag.body }}
                  />
                </div>
              ))}
            </section>

            {/* Section 9 — Worked example */}
            <section id="worked-example" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Worked example: translating a real resource table
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Here is the kind of resource table you will see in a real
                report, followed by a translation into what it actually tells
                you.
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
                        Au (g/t)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Contained Au (oz)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        Ag (g/t)
                      </th>
                      <th className="border border-slate-700 px-3 py-2 text-gold-400">
                        AuEq (g/t)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="text-center">
                    <tr>
                      <td className="border border-slate-700 px-3 py-2">
                        Indicated
                      </td>
                      <td className="border border-slate-700 px-3 py-2">3.4</td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.92
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        100,500
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        38.4
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.41
                      </td>
                    </tr>
                    <tr className="bg-slate-800/50">
                      <td className="border border-slate-700 px-3 py-2">
                        Inferred
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        12.1
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        0.81
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        315,000
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        29.7
                      </td>
                      <td className="border border-slate-700 px-3 py-2">
                        1.19
                      </td>
                    </tr>
                  </tbody>
                </table>
                <p className="text-xs text-slate-500 italic mt-1">
                  Cut-off: 0.40 g/t AuEq. AuEq calculated at $2,200/oz Au,
                  $27/oz Ag, 92% Au recovery, 80% Ag recovery.
                </p>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                <strong className="text-gold-400">
                  Translation, line by line:
                </strong>
              </p>
              <ul className="list-disc pl-6 space-y-3 text-slate-300 mb-4">
                <li>
                  <strong>Total resource is 75% Inferred by ounces.</strong>{" "}
                  (315,000 / (100,500 + 315,000) = 76%). This is an early-stage
                  deposit. The economic case rests on confirming the Inferred
                  portion with infill drilling.
                </li>
                <li>
                  <strong>Grade is modest.</strong> Sub-1 g/t gold is on the low
                  end for underground mining and middle-of-pack for open-pit.
                  AuEq of 1.4 g/t Indicated is workable for open-pit if strip
                  ratio is reasonable.
                </li>
                <li>
                  <strong>
                    AuEq calculation reveals an embedded assumption.
                  </strong>{" "}
                  The gold-equivalent figure uses $2,200/oz Au and $27/oz Ag. If
                  those prices fall, the AuEq figure falls — and the effective
                  cut-off rises, which can shrink the resource. Note that the
                  cut-off (0.40 g/t AuEq) is applied AFTER the conversion, so
                  prices flow through the entire estimate.
                </li>
                <li>
                  <strong>Silver is a non-trivial contributor.</strong> The AuEq
                  is roughly 50% higher than the Au grade alone, meaning silver
                  adds about half the headline grade. If you assumed this was a
                  pure gold deposit, you would be over-pricing it.
                </li>
                <li>
                  <strong>Recovery assumptions need backing.</strong> 92% Au
                  recovery is achievable for free-milling gold but optimistic
                  for refractory ores. Check Item 13 for the metallurgical test
                  work.
                </li>
              </ul>
              <p className="text-slate-300 mb-4 leading-relaxed">
                None of this means the project is bad. It means the headline
                resource number conceals five embedded assumptions, any one of
                which can move the economics meaningfully. This is what
                &quot;reading&quot; a resource table actually looks like.
              </p>
            </section>

            {/* Section 10 — Common mistakes */}
            <section id="common-mistakes" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Common mistakes retail investors make
              </h2>
              <ul className="space-y-4 text-slate-300">
                <li>
                  <strong className="text-gold-400">
                    Treating the press release as the report.
                  </strong>{" "}
                  Press releases are written by IR teams to drive a stock
                  reaction. The report is written by the QP to satisfy the
                  regulator. Always go to the source.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Comparing global resources across deposits.
                  </strong>{" "}
                  &quot;5 million ounces vs 3 million ounces&quot; means nothing
                  without category mix, grade, mining method, and jurisdiction.
                  A 3 Moz deposit at 5 g/t in Canada is worth more than a 5 Moz
                  deposit at 0.6 g/t in a high-risk jurisdiction.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Confusing PEA economics with bankable economics.
                  </strong>{" "}
                  PEAs are scoping studies with ±30% accuracy and can use
                  Inferred Resources. The headline NPV of a PEA is an
                  indication, not a forecast. Discount it accordingly.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Ignoring effective dates.
                  </strong>{" "}
                  A two-year-old resource estimate may bear little resemblance
                  to current geology after subsequent drilling. Check what has
                  been published since.
                </li>
                <li>
                  <strong className="text-gold-400">
                    Assuming reserve = profit.
                  </strong>{" "}
                  Even Proven + Probable Reserves can become uneconomic if metal
                  prices fall or costs rise. Reserves are a function of price
                  assumptions; they shrink and grow with the market.
                </li>
              </ul>
            </section>

            {/* Section 11 — Tools */}
            <section id="tools" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Tools to speed this up
              </h2>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Reading an NI 43-101 from scratch takes 20–30 minutes once you
                know what you are looking for. We built tools to make the
                process faster:
              </p>
              <div className="grid md:grid-cols-2 gap-4 my-6">
                <Link
                  href="/investor-tools/ni43-101-analyzer"
                  className="block bg-slate-800 border border-gold-500/40 hover:border-gold-500 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    NI 43-101 Analyzer →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    AI-assisted extraction of resource tables, economic
                    summaries, and Qualified Person info from any uploaded
                    technical report.
                  </p>
                </Link>
                <Link
                  href="/investor-tools/drill-scanner"
                  className="block bg-slate-800 border border-slate-700 hover:border-gold-500/50 rounded-lg p-5 transition-colors"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-2">
                    Drill Scanner →
                  </h3>
                  <p className="text-sm text-slate-300 mb-0">
                    Scan recent drill press releases across the database. Filter
                    by grade-times-width to find real catalysts vs. noise.
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
                    Compare resource grades across the 500+ company database.
                    Sort by category-weighted grade to filter for serious
                    deposits.
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
                    Browse 500+ junior miners. Each company page links to its
                    most recent NI 43-101 reports, resource estimates, and news
                    releases.
                  </p>
                </Link>
              </div>
              <p className="text-slate-300 mb-4 leading-relaxed">
                Where to find raw reports:{" "}
                <a
                  href="https://www.sedarplus.ca"
                  className="text-gold-400 hover:underline"
                  rel="nofollow noopener"
                  target="_blank"
                >
                  SEDAR+
                </a>{" "}
                is the Canadian filing system; every NI 43-101 must be filed
                there. Most companies also link reports from their IR pages.
              </p>
            </section>

            {/* Section 12 — FAQ */}
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
                  <p
                    className="text-slate-300 mb-0 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: qa.acceptedAnswer.text }}
                  />
                </div>
              ))}
            </section>

            {/* Related guides */}
            <section className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-4">
                Related guides
              </h2>
              <ul className="space-y-3">
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
                    href="/guides/critical-minerals-guide"
                    className="text-gold-400 hover:underline"
                  >
                    Critical Minerals Investment Guide →
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
