import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SiteNav from "@/components/SiteNav";
import {
  GLOSSARY_CATEGORIES,
  fetchGlossaryTerms,
  termAnchor,
  type GlossaryTerm,
} from "@/lib/glossaryCategories";
import { TERM_EXTRAS, termPageAnchors } from "@/lib/glossaryTermExtras";

const BASE = "https://juniorminingintelligence.com";

export const revalidate = 3600;

/**
 * Only terms with expanded context get a page.
 *
 * The stored definitions average 40 words; a page built on one alone would be
 * thin, which is why the category pages came first. A term without an entry in
 * TERM_EXTRAS stays on its category page and is never submitted.
 */
export function generateStaticParams() {
  return termPageAnchors().map((term) => ({ term }));
}

/** All terms across every category, so an anchor can be resolved to its row. */
async function loadAllTerms(): Promise<GlossaryTerm[]> {
  const perCategory = await Promise.all(
    GLOSSARY_CATEGORIES.map((c) => fetchGlossaryTerms(c.apiCategory)),
  );
  return perCategory.flat();
}

async function resolve(anchor: string) {
  const all = await loadAllTerms();
  const term = all.find((t) => termAnchor(t.term) === anchor) ?? null;
  if (!term) return null;
  const category =
    GLOSSARY_CATEGORIES.find((c) => c.apiCategory === term.category) ?? null;
  return { term, category, all };
}

type Props = { params: Promise<{ term: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { term: anchor } = await params;
  const extra = TERM_EXTRAS[anchor];
  if (!extra) return { title: "Not Found" };

  const resolved = await resolve(anchor);
  if (!resolved) return { title: "Not Found" };

  const canonical = `${BASE}/glossary/${anchor}`;
  const title = `${resolved.term.term} — Mining Term Explained`;
  const description = extra.summary || resolved.term.definition.slice(0, 155);

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      url: canonical,
      type: "article",
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

export default async function GlossaryTermPage({ params }: Props) {
  const { term: anchor } = await params;
  const extra = TERM_EXTRAS[anchor];
  if (!extra) notFound();

  const resolved = await resolve(anchor);
  if (!resolved) {
    // The anchor has an expansion but no matching row. That means the term was
    // renamed or removed in the database, and shipping a page with an
    // expansion and no definition would be worse than failing the build.
    throw new Error(
      `Glossary term "${anchor}" has expanded content but no matching row in ` +
        `the database — rename the key in TERM_EXTRAS or restore the term.`,
    );
  }

  const { term, category, all } = resolved;
  const canonical = `${BASE}/glossary/${anchor}`;

  const seeAlso = (extra.seeAlso || [])
    .map((a) => all.find((t) => termAnchor(t.term) === a))
    .filter(Boolean) as GlossaryTerm[];

  // Other terms in the same category, for onward navigation.
  const siblings = all
    .filter(
      (t) => t.category === term.category && termAnchor(t.term) !== anchor,
    )
    .slice(0, 12);

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "DefinedTerm",
        "@id": canonical,
        name: term.term,
        description: term.definition,
        url: canonical,
        ...(category && {
          inDefinedTermSet: {
            "@type": "DefinedTermSet",
            name: category.h1,
            url: `${BASE}/glossary/category/${category.slug}`,
          },
        }),
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
          ...(category
            ? [
                {
                  "@type": "ListItem",
                  position: 3,
                  name: category.label,
                  item: `${BASE}/glossary/category/${category.slug}`,
                },
              ]
            : []),
          {
            "@type": "ListItem",
            position: category ? 4 : 3,
            name: term.term,
            item: canonical,
          },
        ],
      },
    ],
  };

  const sections: [string, string | undefined][] = [
    ["Why it matters", extra.whyItMatters],
    ["In practice", extra.inPractice],
    ["Where people go wrong", extra.pitfall],
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      <SiteNav />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-slate-500 mb-6">
          <Link href="/" className="hover:text-gold-400">
            Home
          </Link>
          <span className="mx-2">/</span>
          <Link href="/glossary" className="hover:text-gold-400">
            Glossary
          </Link>
          {category && (
            <>
              <span className="mx-2">/</span>
              <Link
                href={`/glossary/category/${category.slug}`}
                className="hover:text-gold-400"
              >
                {category.label}
              </Link>
            </>
          )}
        </nav>

        <h1 className="text-3xl sm:text-4xl font-bold text-gold-400 mb-5">
          {term.term}
        </h1>

        {extra.summary && (
          <p className="text-lg text-slate-200 leading-relaxed mb-6">
            {extra.summary}
          </p>
        )}

        <div className="rounded-lg border border-slate-700 bg-slate-800/40 p-5 mb-10">
          <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-2">
            Definition
          </h2>
          <p className="text-slate-300 leading-relaxed">{term.definition}</p>
        </div>

        <div className="flex flex-col gap-9">
          {sections.map(([heading, body]) =>
            body ? (
              <section key={heading}>
                <h2 className="text-2xl font-bold text-gold-400 mb-3">
                  {heading}
                </h2>
                <p className="text-slate-300 leading-relaxed">{body}</p>
              </section>
            ) : null,
          )}
        </div>

        {seeAlso.length > 0 && (
          <section className="mt-12">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">See also</h2>
            <ul className="flex flex-col gap-3">
              {seeAlso.map((t) => (
                <li key={t.id}>
                  <Link
                    href={`/glossary/${termAnchor(t.term)}`}
                    className="text-gold-400 hover:underline font-medium"
                  >
                    {t.term}
                  </Link>
                  <span className="text-slate-400">
                    {" "}
                    — {t.definition.slice(0, 110)}…
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {category && (
          <section className="mt-12 pt-10 border-t border-slate-800">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              More {category.label.toLowerCase()} terms
            </h2>
            <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
              {siblings.map((t) => (
                <Link
                  key={t.id}
                  href={`/glossary/category/${category.slug}#${termAnchor(t.term)}`}
                  className="text-slate-300 hover:text-gold-400"
                >
                  {t.term}
                </Link>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 mt-6">
              <Link
                href={`/glossary/category/${category.slug}`}
                className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
              >
                All {category.label.toLowerCase()} terms →
              </Link>
              <Link
                href="/glossary"
                className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
              >
                Full A–Z glossary →
              </Link>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
