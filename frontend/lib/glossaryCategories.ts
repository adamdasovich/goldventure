/**
 * Glossary category landing pages.
 *
 * The glossary holds 112 terms whose definitions average 255 characters --
 * roughly 40 words. A page per term would be 40 words of unique content
 * wrapped in boilerplate, which is the thin-content pattern that put 154 pages
 * into "crawled, currently not indexed" in the first place. Grouping by
 * category instead gives six pages carrying 377-1,380 words of definitions
 * each, plus an intro written for the group.
 *
 * The slugs deliberately do not match the raw category values: "general" is
 * meaningless as a search target, while "metals-and-materials" is what someone
 * actually types. `apiCategory` keeps the mapping honest.
 */

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

/** Below this many terms a category page is too thin to submit. */
export const MIN_INDEXABLE_TERMS = 5;

export type GlossaryCategory = {
  /** URL slug */
  slug: string;
  /** The `category` value the API stores */
  apiCategory: string;
  /** Short label for nav and breadcrumbs */
  label: string;
  /** H1 */
  h1: string;
  /** Meta description */
  description: string;
  /** Unique intro prose -- two paragraphs. */
  intro: string[];
  /** Cross-links out to guides and listings that fit this category. */
  related: { href: string; text: string }[];
};

export const GLOSSARY_CATEGORIES: GlossaryCategory[] = [
  {
    slug: "resource-reporting",
    apiCategory: "reporting",
    label: "Resource Reporting",
    h1: "Mineral Resource & Reserve Reporting Terms",
    description:
      "Definitions of the resource and reserve categories used in NI 43-101 disclosure — measured, indicated, inferred, proven, probable — and the units they are reported in.",
    intro: [
      "Resource reporting is where most of the confusion in junior mining investing lives. The categories are not interchangeable: an inferred resource rests on limited drilling and cannot legally be converted straight into a reserve, while a proven reserve has survived an economic study. Two companies can quote similar ounce counts and mean very different things by them.",
      "The terms below cover the classification ladder, the study stages that move a project up it, and the equivalence measures — copper equivalent, silver ounce equivalent, total rare earth oxides — that let polymetallic deposits be quoted as a single number. Read the definitions alongside the actual disclosure, because the categories are defined by confidence, not by size.",
    ],
    related: [
      {
        href: "/guides/how-to-read-ni-43-101-report",
        text: "How to read an NI 43-101 report",
      },
      {
        href: "/guides/inferred-vs-indicated-vs-measured-resources",
        text: "Inferred vs indicated vs measured resources",
      },
      { href: "/guides/gold-grade-explained", text: "Gold grade explained" },
    ],
  },
  {
    slug: "geology",
    apiCategory: "geology",
    label: "Geology",
    h1: "Mining Geology Terms & Deposit Types",
    description:
      "Definitions of the deposit types, grade measures and drill-result terms used in junior mining — porphyry, epithermal, VMS, orogenic gold, cut-off grade, true width and more.",
    intro: [
      "Deposit type governs almost everything else about a mining project: the grades you should expect, how the ore is processed, how deep it sits, and how much of it a drill hole actually proves. A 1 g/t intercept is unremarkable in a bulk-tonnage porphyry and excellent in a narrow orogenic gold vein. The vocabulary below is what lets you tell which situation you are reading about.",
      "The list also covers the terms that decide whether a drill result means anything — true width against downhole length, strike length, cut-off grade, and the alteration signatures that suggest a system is bigger than what has been drilled so far. These are the words that appear in every exploration release, usually without explanation.",
    ],
    related: [
      {
        href: "/guides/how-to-interpret-mining-drill-results",
        text: "How to interpret drill results",
      },
      {
        href: "/guides/gold-grade-explained",
        text: "What counts as a good gold grade",
      },
      { href: "/investor-tools/drill-scanner", text: "Drill Result Scanner" },
    ],
  },
  {
    slug: "mining-operations",
    apiCategory: "operations",
    label: "Operations",
    h1: "Mining & Processing Operations Terms",
    description:
      "Definitions of mining and metallurgical terms — open-pit and underground methods, flotation, heap leaching, recovery, stripping ratio, tailings, and battery-chemical products.",
    intro: [
      "Between an orebody and a saleable product sits a processing route, and it is usually the part of the story a junior explains least well. Recovery rate, stripping ratio and concentrate grade often matter more to project economics than the headline resource does — a high-grade deposit with poor metallurgy can be worth less than a lower-grade one that leaches cleanly.",
      "This is also where the battery-metals supply chain gets specific. Lithium carbonate and lithium hydroxide are not the same product and do not serve the same cathode chemistries; nickel sulphate and Class 1 nickel are distinct from the nickel that goes into stainless steel. The terms below cover both conventional mining and the downstream chemical steps.",
    ],
    related: [
      {
        href: "/guides/critical-minerals-guide",
        text: "Critical minerals guide",
      },
      { href: "/companies/commodity/lithium", text: "Lithium companies" },
      { href: "/companies/commodity/nickel", text: "Nickel companies" },
    ],
  },
  {
    slug: "mining-finance",
    apiCategory: "finance",
    label: "Finance",
    h1: "Junior Mining Finance Terms",
    description:
      "Definitions of the financing and valuation terms used by junior miners — private placements, flow-through shares, warrants, AISC, NPV, IRR and payback period.",
    intro: [
      "Junior explorers have no revenue, so they fund themselves by issuing shares. That single fact drives most of the vocabulary here: private placements, flow-through shares, warrants and the dilution they create are the mechanics of how these companies stay alive between discoveries, and how existing shareholders get diluted along the way.",
      "The rest of the list covers how a project gets valued once it is advanced enough to model — NPV, IRR, payback period, and the all-in sustaining cost that determines whether a producer makes money at a given metal price. Understanding a warrant's strike price and expiry tells you where future selling pressure sits long before it arrives.",
    ],
    related: [
      {
        href: "/guides/how-junior-mining-companies-raise-money",
        text: "How junior miners raise money",
      },
      {
        href: "/guides/private-placements-and-warrants",
        text: "Private placements and warrants",
      },
      { href: "/investor-tools/warrant-radar", text: "Warrant Overhang Radar" },
      { href: "/open-financings", text: "Open financings" },
    ],
  },
  {
    slug: "metals-and-materials",
    apiCategory: "general",
    label: "Metals & Materials",
    h1: "Mining Metals & Materials Glossary",
    description:
      "Definitions of the metals and materials junior miners target — battery metals, rare earths, critical minerals, and the specialty metals behind them.",
    intro: [
      "Which metal a company is chasing shapes the entire investment case: who buys it, whether a price is publicly quoted, and how exposed the supply chain is to a single country. Rare earths and battery metals in particular trade very differently from gold, because much of the value sits in downstream separation and refining rather than in the rock.",
      "The terms below cover the individual metals — neodymium, praseodymium, dysprosium, antimony, tungsten, vanadium, indium, molybdenum — and the umbrella categories they get grouped under, which are used loosely and often inconsistently. Knowing the difference between a magnet rare earth and total rare earth oxide is the difference between reading a deposit correctly and not.",
    ],
    related: [
      {
        href: "/guides/critical-minerals-guide",
        text: "Critical minerals guide",
      },
      {
        href: "/companies/commodity/critical-minerals",
        text: "Critical minerals companies",
      },
      {
        href: "/companies/commodity/rare-earths",
        text: "Rare earth companies",
      },
      { href: "/metals", text: "Live metals prices" },
    ],
  },
  {
    slug: "regulation-and-standards",
    apiCategory: "regulatory",
    label: "Regulation & Standards",
    h1: "Mining Disclosure Regulation & Standards",
    description:
      "Definitions of the rules governing mining disclosure — NI 43-101, the qualified person requirement, and the critical and strategic minerals designations.",
    intro: [
      "Mining disclosure in Canada is governed by NI 43-101, which exists because the sector has a long history of unverifiable claims. It requires technical information to be prepared or approved by a qualified person with defined credentials and accountability, which is what separates a resource estimate from a press release.",
      "The remainder of this group covers government designations — critical minerals lists, strategic and defense metals — that increasingly determine which projects attract state funding and permitting support. These labels are policy instruments rather than geological ones, and they change with the list that issues them.",
    ],
    related: [
      {
        href: "/guides/how-to-read-ni-43-101-report",
        text: "How to read an NI 43-101 report",
      },
      {
        href: "/guides/critical-minerals-guide",
        text: "Critical minerals guide",
      },
    ],
  },
];

export function getGlossaryCategory(slug: string): GlossaryCategory | null {
  return GLOSSARY_CATEGORIES.find((c) => c.slug === slug) ?? null;
}

export type GlossaryTerm = {
  id: number;
  term: string;
  definition: string;
  category: string;
  related_links?: { url: string; text: string }[] | null;
  keywords?: string | null;
};

/** Turn a term into a stable anchor id, e.g. "Grade (g/t)" -> "grade-g-t". */
export function termAnchor(term: string): string {
  return term
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Every term in one category, alphabetical.
 *
 * `fresh` bypasses the long cache. Pages leave it false -- they carry their own
 * revalidate and a glossary an hour stale is harmless. The sitemap passes true,
 * for the same reason the commodity facets do: Next persists fetch results
 * across builds, so a cached read would decide inclusion from stale counts.
 */
export async function fetchGlossaryTerms(
  apiCategory: string,
  fresh = false,
): Promise<GlossaryTerm[]> {
  let terms: GlossaryTerm[] = [];
  let page = 1;
  let hasMore = true;
  while (hasMore) {
    const url = `${API_BASE_URL}/glossary/?category=${encodeURIComponent(apiCategory)}&page=${page}&page_size=100`;
    const init = fresh
      ? { next: { revalidate: 60 } }
      : { next: { revalidate: 3600 } };

    // Retry rather than swallow. Silently returning [] on a network blip bakes
    // an empty page into the static build for an hour and drops the category
    // out of the sitemap -- which is exactly what happened on the first build
    // of these pages: five of six came out blank after one ConnectTimeoutError.
    let data: any = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const res = await fetch(url, init);
        if (!res.ok) break;
        data = await res.json();
        break;
      } catch {
        if (attempt === 2) break;
        await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
      }
    }
    if (!data) break;

    const results: GlossaryTerm[] =
      data.results || (Array.isArray(data) ? data : []);
    terms = [...terms, ...results];
    hasMore = !!data.next;
    page++;
  }

  // The API filter is not guaranteed to be exact, and two terms are stored
  // twice under slightly different names (VMS, Qualified Person). Dedupe on the
  // anchor so a page never lists the same heading twice.
  const seen = new Set<string>();
  return terms
    .filter((t) => {
      if (!t.term || t.category !== apiCategory) return false;
      const key = termAnchor(t.term);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => a.term.localeCompare(b.term));
}

/** Categories with enough terms to be worth submitting to the sitemap. */
export async function indexableGlossaryCategories(): Promise<
  GlossaryCategory[]
> {
  const counted = await Promise.all(
    GLOSSARY_CATEGORIES.map(async (category) => ({
      category,
      count: (await fetchGlossaryTerms(category.apiCategory, true)).length,
    })),
  );
  return counted
    .filter((c) => c.count >= MIN_INDEXABLE_TERMS)
    .map((c) => c.category);
}
