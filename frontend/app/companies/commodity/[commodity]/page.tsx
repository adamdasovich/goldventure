import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { companyHref } from "@/lib/companyUrl";
import {
  ALL_FACETS,
  CRITICAL,
  FACETS,
  MIN_INDEXABLE,
  fetchFacetCompanies,
  getFacet,
} from "@/lib/commodityFacets";
import SiteNav from "@/components/SiteNav";

const BASE = "https://juniorminingintelligence.com";

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
  const companies = await fetchFacetCompanies(facet.query);
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

  const companies = await fetchFacetCompanies(facet.query);
  const canonical = `${BASE}/companies/commodity/${facet.slug}`;

  // Other facets to cross-link (internal linking spreads authority).
  const otherFacets = ALL_FACETS.filter(
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
      <SiteNav />
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

            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-slate-50 mb-6 tracking-tight">
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
                  className="px-4 py-2.5 min-h-11 inline-flex items-center rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
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
