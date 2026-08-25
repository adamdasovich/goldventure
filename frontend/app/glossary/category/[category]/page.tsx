import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  GLOSSARY_CATEGORIES,
  MIN_INDEXABLE_TERMS,
  fetchGlossaryTerms,
  getGlossaryCategory,
  termAnchor,
} from "@/lib/glossaryCategories";
import SiteNav from "@/components/SiteNav";
import { hasTermPage } from "@/lib/glossaryTermExtras";

const BASE = "https://juniorminingintelligence.com";

export const revalidate = 3600;

export function generateStaticParams() {
  return GLOSSARY_CATEGORIES.map((c) => ({ category: c.slug }));
}

type Props = { params: Promise<{ category: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category: slug } = await params;
  const category = getGlossaryCategory(slug);
  if (!category) return { title: "Not Found" };

  const terms = await fetchGlossaryTerms(category.apiCategory);
  const canonical = `${BASE}/glossary/category/${category.slug}`;
  const title = `${category.h1} — ${terms.length} Definitions`;

  return {
    title,
    description: category.description,
    alternates: { canonical },
    // A category too small to be useful should not be submitted, the same rule
    // the commodity facets use.
    ...(terms.length < MIN_INDEXABLE_TERMS && {
      robots: { index: false, follow: true },
    }),
    openGraph: {
      title,
      description: category.description,
      url: canonical,
      type: "website",
      siteName: "Junior Mining Intelligence",
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description: category.description,
      images: ["/og-image.png"],
    },
  };
}

export default async function GlossaryCategoryPage({ params }: Props) {
  const { category: slug } = await params;
  const category = getGlossaryCategory(slug);
  if (!category) notFound();

  const terms = await fetchGlossaryTerms(category.apiCategory);

  // Fail the build rather than ship an empty page. Every category has at least
  // seven terms, so zero means the fetch failed -- and the first build of these
  // pages shipped five of six blank because the helper swallowed the error and
  // returned []. A broken deploy is cheap to notice; a silently empty indexed
  // page is not.
  if (terms.length === 0) {
    throw new Error(
      `Glossary category "${category.slug}" returned no terms — refusing to ` +
        `render an empty page. Check the API at ${process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL}.`,
    );
  }

  const canonical = `${BASE}/glossary/category/${category.slug}`;
  const others = GLOSSARY_CATEGORIES.filter((c) => c.slug !== category.slug);

  // DefinedTermSet is the schema.org type built for exactly this page: a named
  // collection of definitions. Emitted from the server component so it is in
  // the HTML rather than assembled after hydration.
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "DefinedTermSet",
        "@id": canonical,
        name: category.h1,
        description: category.description,
        url: canonical,
        hasDefinedTerm: terms.map((t) => ({
          "@type": "DefinedTerm",
          name: t.term,
          description: t.definition,
          url: `${canonical}#${termAnchor(t.term)}`,
        })),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Home", item: BASE },
          {
            "@type": "ListItem",
            position: 2,
            name: "Glossary",
            item: `${BASE}/glossary`,
          },
          {
            "@type": "ListItem",
            position: 3,
            name: category.label,
            item: canonical,
          },
        ],
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <SiteNav />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* breadcrumb */}
        <nav aria-label="Breadcrumb" className="text-sm text-slate-500 mb-6">
          <Link href="/" className="hover:text-gold-400">
            Home
          </Link>
          <span className="mx-2">/</span>
          <Link href="/glossary" className="hover:text-gold-400">
            Glossary
          </Link>
          <span className="mx-2">/</span>
          <span className="text-slate-400">{category.label}</span>
        </nav>

        <header className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gold-400 mb-5">
            {category.h1}
          </h1>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            {category.intro.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
          <p className="text-slate-500 text-sm mt-5">
            {terms.length} term{terms.length === 1 ? "" : "s"} in this section.
          </p>
        </header>

        {/* jump list — doubles as the deep-link targets for each term */}
        {terms.length > 6 && (
          <nav
            aria-label="Terms in this section"
            className="mb-10 p-5 rounded-lg border border-slate-700 bg-slate-800/40"
          >
            <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-3">
              On this page
            </h2>
            <ul className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
              {terms.map((t) => (
                <li key={t.id}>
                  <a
                    href={`#${termAnchor(t.term)}`}
                    className="text-slate-300 hover:text-gold-400"
                  >
                    {t.term}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}

        {/* the definitions */}
        <div className="flex flex-col gap-8">
          {terms.map((t) => (
            <section
              key={t.id}
              id={termAnchor(t.term)}
              className="scroll-mt-24"
            >
              <h2 className="text-xl font-semibold text-slate-100 mb-2">
                {/*
                  Terms with expanded context get their own page; the rest are
                  only ever read here. Linking from the heading is what makes
                  those pages reachable by a crawler at all.
                */}
                {hasTermPage(termAnchor(t.term)) ? (
                  <Link
                    href={`/glossary/${termAnchor(t.term)}`}
                    className="hover:text-gold-400"
                  >
                    {t.term}
                  </Link>
                ) : (
                  t.term
                )}
              </h2>
              <p className="text-slate-300 leading-relaxed">{t.definition}</p>
              {Array.isArray(t.related_links) && t.related_links.length > 0 && (
                <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm">
                  {t.related_links.map((l, i) => (
                    <li key={i}>
                      <Link
                        href={l.url}
                        className="text-gold-400 hover:underline"
                      >
                        {l.text} →
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>

        {/* further reading */}
        {category.related.length > 0 && (
          <section className="mt-14">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              Further reading
            </h2>
            <div className="flex flex-wrap gap-3">
              {category.related.map((r) => (
                <Link
                  key={r.href}
                  href={r.href}
                  className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
                >
                  {r.text} →
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* the other categories */}
        <section className="mt-12 pt-10 border-t border-slate-800">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            Other sections of the glossary
          </h2>
          <div className="flex flex-wrap gap-3">
            {others.map((c) => (
              <Link
                key={c.slug}
                href={`/glossary/category/${c.slug}`}
                className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
              >
                {c.label}
              </Link>
            ))}
            <Link
              href="/glossary"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Full A–Z glossary
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
