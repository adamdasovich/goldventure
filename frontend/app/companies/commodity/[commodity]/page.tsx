import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { companyHref } from "@/lib/companyUrl";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const BASE = "https://juniorminingintelligence.com";

// Below this, the facet page is too thin to be worth indexing — we still render
// it for users but tell Google not to index (avoids creating new soft-404s /
// "crawled - currently not indexed" pages, which is the whole problem we're
// trying to fix elsewhere).
const MIN_INDEXABLE = 3;

type FacetConfig = {
  /** URL slug */
  slug: string;
  /** Human label, e.g. "Gold" */
  label: string;
  /** Exact primary_commodity values to query — the API match is case-sensitive
   *  (`__in`), so include realistic casing + synonyms. */
  query: string[];
  /** H1 */
  h1: string;
  /** Unique intro prose — the SEO payload. Two short paragraphs. */
  intro: string[];
};

// Keep this list tight and high-intent. Each entry is a real search target.
const FACETS: Record<string, FacetConfig> = {
  gold: {
    slug: "gold",
    label: "Gold",
    query: ["Gold", "gold", "GOLD", "Au"],
    h1: "Gold Mining Companies & Junior Gold Stocks",
    intro: [
      "Junior gold companies are the exploration and development-stage miners searching for the next economic gold deposit — typically listed on the TSX Venture Exchange (TSXV), TSX, or comparable junior boards, with market caps well under $500M. They carry more risk than producers but offer the leverage that draws investors to the sector.",
      "The companies below all have at least one gold-focused project in our database. Each profile tracks projects, resource estimates, drill results, financings, and press releases. Use it to compare grade, jurisdiction, and stage across the junior gold space.",
    ],
  },
  silver: {
    slug: "silver",
    label: "Silver",
    query: ["Silver", "silver", "SILVER", "Ag"],
    h1: "Silver Mining Companies & Junior Silver Stocks",
    intro: [
      "Junior silver companies explore for and develop primary silver deposits, as well as silver-rich polymetallic systems where silver is credited alongside lead, zinc, or gold. Silver's dual role as a monetary and industrial metal makes the juniors especially sensitive to both precious-metals sentiment and solar/electronics demand.",
      "Every company below has a silver-focused project on file. Compare grades (usually reported in g/t Ag), resource categories, and jurisdictions across the group, and drill into each profile for financings and the latest exploration news.",
    ],
  },
  copper: {
    slug: "copper",
    label: "Copper",
    query: ["Copper", "copper", "COPPER", "Cu"],
    h1: "Copper Mining Companies & Junior Copper Stocks",
    intro: [
      "Copper juniors sit at the center of the electrification thesis — every EV, grid upgrade, and data center needs it, and the discovery pipeline for large new deposits is thin. These companies range from grassroots porphyry explorers to advanced developers advancing feasibility-stage projects.",
      "The companies listed here each hold a copper-focused project. Copper grades are quoted as a percentage (e.g. 0.5% Cu) rather than g/t; compare grade, tonnage, and jurisdiction below, then open a profile for resource estimates, financings, and news.",
    ],
  },
  lithium: {
    slug: "lithium",
    label: "Lithium",
    query: ["Lithium", "lithium", "LITHIUM", "Li"],
    h1: "Lithium Mining Companies & Junior Lithium Stocks",
    intro: [
      "Lithium juniors explore two main deposit types: hard-rock spodumene (pegmatites) and lithium brines. As the anode-to-cathode battery supply chain localizes in North America and Europe, junior lithium explorers have become a proxy for EV and grid-storage demand growth.",
      "Each company below has a lithium-focused project. Hard-rock grades are reported as % Li₂O and brines as ppm/mg-L lithium — different units for different deposit styles. Compare stage and jurisdiction here, then open a profile for the full picture.",
    ],
  },
  nickel: {
    slug: "nickel",
    label: "Nickel",
    query: ["Nickel", "nickel", "NICKEL", "Ni"],
    h1: "Nickel Mining Companies & Junior Nickel Stocks",
    intro: [
      "Nickel juniors target sulphide and laterite deposits that feed both stainless steel and the battery supply chain. Class-1 battery-grade nickel is the prize for EV-focused investors, and sulphide discoveries in stable jurisdictions command a premium.",
      "The companies below each hold a nickel-focused project. Compare grade (% Ni), deposit type, and jurisdiction across the group, and open any profile for resource estimates, financings, and exploration updates.",
    ],
  },
  cobalt: {
    slug: "cobalt",
    label: "Cobalt",
    query: ["Cobalt", "cobalt", "COBALT", "Co"],
    h1: "Cobalt Mining Companies & Junior Cobalt Stocks",
    intro: [
      "Cobalt juniors offer exposure to a critical battery metal whose supply is concentrated in the DRC — driving Western investors and automakers toward alternative, ethically sourced deposits. Cobalt is usually a by-product credit in nickel-copper systems rather than a primary target.",
      "Each company here has a cobalt-focused project on file. Review grades, deposit context, and jurisdiction below, then open a profile for the detailed project, financing, and news history.",
    ],
  },
  uranium: {
    slug: "uranium",
    label: "Uranium",
    query: ["Uranium", "uranium", "URANIUM", "U", "U3O8"],
    h1: "Uranium Mining Companies & Junior Uranium Stocks",
    intro: [
      "Uranium juniors have re-rated as nuclear power returns to the clean-energy conversation and the spot price recovers from a decade-long bear market. The Athabasca Basin in Canada hosts the world's highest-grade deposits and dominates junior exploration interest.",
      "The companies below each hold a uranium-focused project. Grades are reported as % U₃O₈ and can vary by orders of magnitude between basin styles. Compare grade, stage, and jurisdiction here, then open a profile for resources, financings, and news.",
    ],
  },
  "rare-earths": {
    slug: "rare-earths",
    label: "Rare Earths",
    query: [
      "Rare Earths",
      "Rare Earth",
      "Rare Earth Elements",
      "REE",
      "rare earths",
      "TREO",
    ],
    h1: "Rare Earth Mining Companies & Junior REE Stocks",
    intro: [
      "Rare earth element (REE) juniors are strategically important because a handful of magnet metals — neodymium, praseodymium, dysprosium, terbium — are essential to EV motors, wind turbines, and defense systems, yet processing is heavily concentrated in China. Western supply-chain independence is the core investment thesis.",
      "Each company below holds a rare-earth-focused project. Grades are usually quoted as total rare earth oxide (% TREO), but the value sits in the magnet-metal split — check each profile. Compare deposit type and jurisdiction here, then dive into the details.",
    ],
  },
  graphite: {
    slug: "graphite",
    label: "Graphite",
    query: ["Graphite", "graphite", "GRAPHITE", "C"],
    h1: "Graphite Mining Companies & Junior Graphite Stocks",
    intro: [
      "Graphite juniors supply the largest single component of a lithium-ion battery by weight — the anode. Natural flake graphite and its downstream conversion to coated spherical purified graphite (CSPG) are the focus for battery-supply-chain investors seeking a China alternative.",
      "The companies below each hold a graphite-focused project. Flake size distribution and purity (% Cg) matter as much as tonnage. Compare across the group here, then open a profile for resource, financing, and news detail.",
    ],
  },
};

// Multi-commodity umbrella facet — points at the critical-minerals guide.
const CRITICAL: FacetConfig = {
  slug: "critical-minerals",
  label: "Critical Minerals",
  query: [
    "Lithium",
    "Copper",
    "Nickel",
    "Cobalt",
    "Graphite",
    "Rare Earths",
    "Rare Earth Elements",
    "REE",
    "Uranium",
    "Manganese",
    "Vanadium",
    "Tin",
  ],
  h1: "Critical Minerals Mining Companies & Junior Stocks",
  intro: [
    "Critical minerals are the metals governments have flagged as essential to energy and defense supply chains yet vulnerable to supply disruption — lithium, copper, nickel, cobalt, graphite, rare earths, uranium, and more. Junior explorers are where most new Western supply will have to come from.",
    "The companies below each hold at least one critical-minerals project. For a primer on the sector and its demand drivers, see our critical minerals guide. Compare commodity, stage, and jurisdiction across the group, then open any profile for the full detail.",
  ],
};

function getFacet(slug: string): FacetConfig | null {
  if (slug === CRITICAL.slug) return CRITICAL;
  return FACETS[slug] ?? null;
}

type Company = {
  id: number;
  name: string;
  slug?: string | null;
  ticker_symbol?: string | null;
  exchange?: string | null;
  brief_description?: string | null;
  headquarters_country?: string | null;
  project_count?: number | null;
};

async function fetchCompanies(query: string[]): Promise<Company[]> {
  const commodity = encodeURIComponent(query.join(","));
  let companies: Company[] = [];
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
      const results: Company[] =
        data.results || (Array.isArray(data) ? data : []);
      companies = [...companies, ...results];
      hasMore = !!data.next;
      page++;
    } catch {
      break;
    }
  }
  // Only surface companies with enough substance to be worth a link.
  return companies
    .filter((c) => c.name)
    .sort((a, b) => a.name.localeCompare(b.name));
}

export const revalidate = 3600;

export function generateStaticParams() {
  return [...Object.keys(FACETS), CRITICAL.slug].map((commodity) => ({
    commodity,
  }));
}

type Props = { params: Promise<{ commodity: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { commodity } = await params;
  const facet = getFacet(commodity);
  if (!facet) return { title: "Not Found" };

  const canonical = `${BASE}/companies/commodity/${facet.slug}`;
  const companies = await fetchCompanies(facet.query);
  const count = companies.length;
  const title = `${facet.label} Mining Companies — ${count > 0 ? `${count} Junior ` : "Junior "}${facet.label} Stocks`;
  const description = `Browse ${count > 0 ? count : "junior"} ${facet.label.toLowerCase()} mining companies and exploration stocks. Projects, resource estimates, drill results, financings, and news across the junior ${facet.label.toLowerCase()} sector.`;

  return {
    title,
    description,
    alternates: { canonical },
    ...(count < MIN_INDEXABLE && { robots: { index: false, follow: true } }),
    openGraph: {
      title,
      description,
      url: canonical,
      type: "website",
      siteName: "Junior Mining Intelligence",
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/og-image.png"],
    },
  };
}

export default async function CommodityFacetPage({ params }: Props) {
  const { commodity } = await params;
  const facet = getFacet(commodity);
  if (!facet) notFound();

  const companies = await fetchCompanies(facet.query);
  const canonical = `${BASE}/companies/commodity/${facet.slug}`;

  // Other facets to cross-link (internal linking spreads authority).
  const otherFacets = [...Object.values(FACETS), CRITICAL].filter(
    (f) => f.slug !== facet.slug,
  );

  const collectionJsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: facet.h1,
    url: canonical,
    description: facet.intro[0],
    isPartOf: { "@type": "WebSite", "@id": `${BASE}/#website` },
    mainEntity: {
      "@type": "ItemList",
      numberOfItems: companies.length,
      itemListElement: companies.slice(0, 50).map((c, i) => ({
        "@type": "ListItem",
        position: i + 1,
        url: `${BASE}${companyHref(c)}`,
        name: c.name,
      })),
    },
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE },
      {
        "@type": "ListItem",
        position: 2,
        name: "Companies",
        item: `${BASE}/companies`,
      },
      { "@type": "ListItem", position: 3, name: facet.label, item: canonical },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />

      <div className="min-h-screen bg-slate-900">
        {/* Header */}
        <div className="bg-gradient-to-b from-slate-800 to-slate-900 border-b border-slate-700">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <nav className="text-sm mb-6">
              <ol className="flex items-center space-x-2 text-slate-400">
                <li>
                  <Link href="/" className="hover:text-gold-400">
                    Home
                  </Link>
                </li>
                <li>/</li>
                <li>
                  <Link href="/companies" className="hover:text-gold-400">
                    Companies
                  </Link>
                </li>
                <li>/</li>
                <li className="text-slate-300">{facet.label}</li>
              </ol>
            </nav>

            <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-6">
              {facet.h1}
            </h1>
            {facet.intro.map((p, i) => (
              <p
                key={i}
                className="text-lg text-slate-300 max-w-3xl mb-4 leading-relaxed"
              >
                {facet.slug === CRITICAL.slug && i === 1 ? (
                  <>
                    The companies below each hold at least one critical-minerals
                    project. For a primer on the sector and its demand drivers,
                    see our{" "}
                    <Link
                      href="/guides/critical-minerals-guide"
                      className="text-gold-400 hover:underline"
                    >
                      critical minerals guide
                    </Link>
                    . Compare commodity, stage, and jurisdiction across the
                    group, then open any profile for the full detail.
                  </>
                ) : (
                  p
                )}
              </p>
            ))}
            <p className="text-slate-400 mt-2">
              {companies.length} {facet.label.toLowerCase()}
              {companies.length === 1 ? " company" : " companies"} in our
              database.
            </p>
          </div>
        </div>

        {/* Company list */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          {companies.length === 0 ? (
            <div className="text-slate-400">
              We&apos;re still building out coverage for{" "}
              {facet.label.toLowerCase()} companies.{" "}
              <Link href="/companies" className="text-gold-400 hover:underline">
                Browse all companies →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {companies.map((c) => (
                <Link
                  key={c.id}
                  href={companyHref(c)}
                  className="block glass-card rounded-lg border border-slate-700 hover:border-gold-500/50 p-5 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="text-lg font-semibold text-slate-100">
                      {c.name}
                    </h2>
                    {c.ticker_symbol && (
                      <span className="text-xs px-2 py-1 rounded bg-slate-700/50 text-gold-400 whitespace-nowrap">
                        {c.exchange
                          ? `${c.exchange.toUpperCase()}: ${c.ticker_symbol}`
                          : c.ticker_symbol}
                      </span>
                    )}
                  </div>
                  {c.brief_description && (
                    <p className="text-sm text-slate-400 mt-2 line-clamp-3">
                      {c.brief_description}
                    </p>
                  )}
                  {c.headquarters_country && (
                    <p className="text-xs text-slate-500 mt-3">
                      {c.headquarters_country}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Cross-links to other commodity facets */}
        <div className="bg-slate-800/50 border-t border-slate-700">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <h2 className="text-2xl font-bold text-gold-400 mb-5">
              Explore other commodities
            </h2>
            <div className="flex flex-wrap gap-3">
              {otherFacets.map((f) => (
                <Link
                  key={f.slug}
                  href={`/companies/commodity/${f.slug}`}
                  className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
                >
                  {f.label} companies →
                </Link>
              ))}
              <Link
                href="/companies"
                className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
              >
                All companies →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
