/**
 * Commodity landing-page facets.
 *
 * Shared by `app/companies/commodity/[commodity]/page.tsx` (which renders them)
 * and `app/sitemap.ts` (which decides whether to submit them). Keeping one
 * source of truth is the point: the two lists previously drifted, and the
 * sitemap ended up submitting URLs that self-applied `noindex` — a page that is
 * both submitted and noindexed is a direct quality signal against the domain.
 */

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

/** Below this many companies a facet is too thin to index or submit. */
export const MIN_INDEXABLE = 3;

export type FacetConfig = {
  /** URL slug */
  slug: string;
  /** Human label, e.g. "Gold" */
  label: string;
  /**
   * `primary_commodity` values to match. The API compares case-insensitively
   * (`__iexact`), so casing here is cosmetic — but genuine synonyms
   * ("REE" vs "Rare Earths") still have to be listed explicitly.
   */
  query: string[];
  /** H1 */
  h1: string;
  /** Unique intro prose — the SEO payload. Two short paragraphs. */
  intro: string[];
};

// Keep this list tight and high-intent. Each entry is a real search target.
export const FACETS: Record<string, FacetConfig> = {
  gold: {
    slug: "gold",
    label: "Gold",
    query: ["gold", "au"],
    h1: "Gold Mining Companies & Junior Gold Stocks",
    intro: [
      "Junior gold companies are the exploration and development-stage miners searching for the next economic gold deposit — typically listed on the TSX Venture Exchange (TSXV), TSX, or comparable junior boards, with market caps well under $500M. They carry more risk than producers but offer the leverage that draws investors to the sector.",
      "The companies below all have at least one gold-focused project in our database. Each profile tracks projects, resource estimates, drill results, financings, and press releases. Use it to compare grade, jurisdiction, and stage across the junior gold space.",
    ],
  },
  silver: {
    slug: "silver",
    label: "Silver",
    query: ["silver", "ag"],
    h1: "Silver Mining Companies & Junior Silver Stocks",
    intro: [
      "Junior silver companies explore for and develop primary silver deposits, as well as silver-rich polymetallic systems where silver is credited alongside lead, zinc, or gold. Silver's dual role as a monetary and industrial metal makes the juniors especially sensitive to both precious-metals sentiment and solar/electronics demand.",
      "Every company below has a silver-focused project on file. Compare grades (usually reported in g/t Ag), resource categories, and jurisdictions across the group, and drill into each profile for financings and the latest exploration news.",
    ],
  },
  copper: {
    slug: "copper",
    label: "Copper",
    query: ["copper", "cu"],
    h1: "Copper Mining Companies & Junior Copper Stocks",
    intro: [
      "Copper juniors sit at the center of the electrification thesis — every EV, grid upgrade, and data center needs it, and the discovery pipeline for large new deposits is thin. These companies range from grassroots porphyry explorers to advanced developers advancing feasibility-stage projects.",
      "The companies listed here each hold a copper-focused project. Copper grades are quoted as a percentage (e.g. 0.5% Cu) rather than g/t; compare grade, tonnage, and jurisdiction below, then open a profile for resource estimates, financings, and news.",
    ],
  },
  lithium: {
    slug: "lithium",
    label: "Lithium",
    query: ["lithium", "li"],
    h1: "Lithium Mining Companies & Junior Lithium Stocks",
    intro: [
      "Lithium juniors explore two main deposit types: hard-rock spodumene (pegmatites) and lithium brines. As the anode-to-cathode battery supply chain localizes in North America and Europe, junior lithium explorers have become a proxy for EV and grid-storage demand growth.",
      "Each company below has a lithium-focused project. Hard-rock grades are reported as % Li₂O and brines as ppm/mg-L lithium — different units for different deposit styles. Compare stage and jurisdiction here, then open a profile for the full picture.",
    ],
  },
  nickel: {
    slug: "nickel",
    label: "Nickel",
    query: ["nickel", "ni"],
    h1: "Nickel Mining Companies & Junior Nickel Stocks",
    intro: [
      "Nickel juniors target sulphide and laterite deposits that feed both stainless steel and the battery supply chain. Class-1 battery-grade nickel is the prize for EV-focused investors, and sulphide discoveries in stable jurisdictions command a premium.",
      "The companies below each hold a nickel-focused project. Compare grade (% Ni), deposit type, and jurisdiction across the group, and open any profile for resource estimates, financings, and exploration updates.",
    ],
  },
  cobalt: {
    slug: "cobalt",
    label: "Cobalt",
    query: ["cobalt", "co"],
    h1: "Cobalt Mining Companies & Junior Cobalt Stocks",
    intro: [
      "Cobalt juniors offer exposure to a critical battery metal whose supply is concentrated in the DRC — driving Western investors and automakers toward alternative, ethically sourced deposits. Cobalt is usually a by-product credit in nickel-copper systems rather than a primary target.",
      "Each company here has a cobalt-focused project on file. Review grades, deposit context, and jurisdiction below, then open a profile for the detailed project, financing, and news history.",
    ],
  },
  uranium: {
    slug: "uranium",
    label: "Uranium",
    query: ["uranium", "u3o8"],
    h1: "Uranium Mining Companies & Junior Uranium Stocks",
    intro: [
      "Uranium juniors have re-rated as nuclear power returns to the clean-energy conversation and the spot price recovers from a decade-long bear market. The Athabasca Basin in Canada hosts the world's highest-grade deposits and dominates junior exploration interest.",
      "The companies below each hold a uranium-focused project. Grades are reported as % U₃O₈ and can vary by orders of magnitude between basin styles. Compare grade, stage, and jurisdiction here, then open a profile for resources, financings, and news.",
    ],
  },
  "rare-earths": {
    slug: "rare-earths",
    label: "Rare Earths",
    query: ["rare earths", "rare earth", "rare earth elements", "ree", "treo"],
    h1: "Rare Earth Mining Companies & Junior REE Stocks",
    intro: [
      "Rare earth element (REE) juniors are strategically important because a handful of magnet metals — neodymium, praseodymium, dysprosium, terbium — are essential to EV motors, wind turbines, and defense systems, yet processing is heavily concentrated in China. Western supply-chain independence is the core investment thesis.",
      "Each company below holds a rare-earth-focused project. Grades are usually quoted as total rare earth oxide (% TREO), but the value sits in the magnet-metal split — check each profile. Compare deposit type and jurisdiction here, then dive into the details.",
    ],
  },
  graphite: {
    slug: "graphite",
    label: "Graphite",
    query: ["graphite"],
    h1: "Graphite Mining Companies & Junior Graphite Stocks",
    intro: [
      "Graphite juniors supply the largest single component of a lithium-ion battery by weight — the anode. Natural flake graphite and its downstream conversion to coated spherical purified graphite (CSPG) are the focus for battery-supply-chain investors seeking a China alternative.",
      "The companies below each hold a graphite-focused project. Flake size distribution and purity (% Cg) matter as much as tonnage. Compare across the group here, then open a profile for resource, financing, and news detail.",
    ],
  },
};

// Multi-commodity umbrella facet — points at the critical-minerals guide.
export const CRITICAL: FacetConfig = {
  slug: "critical-minerals",
  label: "Critical Minerals",
  query: [
    "lithium",
    "copper",
    "nickel",
    "cobalt",
    "graphite",
    "rare earths",
    "rare earth",
    "rare earth elements",
    "ree",
    "uranium",
    "manganese",
    "vanadium",
    "tin",
  ],
  h1: "Critical Minerals Mining Companies & Junior Stocks",
  intro: [
    "Critical minerals are the metals governments have flagged as essential to energy and defense supply chains yet vulnerable to supply disruption — lithium, copper, nickel, cobalt, graphite, rare earths, uranium, and more. Junior explorers are where most new Western supply will have to come from.",
    "The companies below each hold at least one critical-minerals project. For a primer on the sector and its demand drivers, see our critical minerals guide. Compare commodity, stage, and jurisdiction across the group, then open any profile for the full detail.",
  ],
};

/** Every facet, in the order they should appear. */
export const ALL_FACETS: FacetConfig[] = [...Object.values(FACETS), CRITICAL];

export function getFacet(slug: string): FacetConfig | null {
  if (slug === CRITICAL.slug) return CRITICAL;
  return FACETS[slug] ?? null;
}

export type FacetCompany = {
  id: number;
  name: string;
  slug?: string | null;
  ticker_symbol?: string | null;
  exchange?: string | null;
  brief_description?: string | null;
  headquarters_country?: string | null;
  project_count?: number | null;
};

/** Fetch every company holding a project in any of `query`, sorted by name. */
export async function fetchFacetCompanies(
  query: string[],
): Promise<FacetCompany[]> {
  const commodity = encodeURIComponent(query.join(","));
  let companies: FacetCompany[] = [];
  let page = 1;
  let hasMore = true;
  while (hasMore) {
    try {
      const res = await fetch(
        `${API_BASE_URL}/companies/?commodity=${commodity}&page=${page}&page_size=100`,
        { next: { revalidate: 3600 } },
      );
      if (!res.ok) break;
      const data = await res.json();
      const results: FacetCompany[] =
        data.results || (Array.isArray(data) ? data : []);
      companies = [...companies, ...results];
      hasMore = !!data.next;
      page++;
    } catch {
      break;
    }
  }
  return companies
    .filter((c) => c.name)
    .sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * Facets with enough companies to be worth submitting. Mirrors the page's own
 * `MIN_INDEXABLE` check, so the sitemap never lists a URL that noindexes itself.
 */
export async function indexableFacets(): Promise<FacetConfig[]> {
  const counted = await Promise.all(
    ALL_FACETS.map(async (facet) => ({
      facet,
      count: (await fetchFacetCompanies(facet.query)).length,
    })),
  );
  return counted.filter((c) => c.count >= MIN_INDEXABLE).map((c) => c.facet);
}
