import type { ReactNode } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import SiteHeader from "@/components/SiteHeader";
import { toolBySlug } from "./tools";

const BASE = "https://juniorminingintelligence.com";

export type ToolFaq = { q: string; a: string };

export type ToolSection = {
  id: string;
  heading: string;
  body: ReactNode;
};

type Props = {
  /** Catalogue slug — drives the breadcrumb and the canonical path. */
  slug: string;
  badge: string;
  title: string;
  /** One or two sentences under the h1. Plain text, no marketing. */
  intro: string;
  /** The interactive tool. Rendered between the header and the content. */
  tool: ReactNode;
  /** Explanatory sections, in reading order. Each becomes an h2. */
  sections: ToolSection[];
  faqs: ToolFaq[];
  /** Slugs of 2-4 related tools. */
  related: string[];
  /** Optional closing paragraph under the related grid. */
  relatedNote?: ReactNode;
};

/**
 * Shared shell for an individual investor-tool page.
 *
 * Every tool page was a single "use client" component rendering 36-106 words:
 * a heading, an interactive widget, and nothing indexable. Google filed
 * several as soft 404s, correctly. This renders the chrome, the explanatory
 * content and the structured data on the server, with the tool itself passed
 * in as a client child.
 *
 * Section content is deliberately supplied per tool rather than templated —
 * eight pages sharing boilerplate prose would be near-duplicate content and
 * would do more harm than the thin pages it replaces.
 */
export default function ToolPageLayout({
  slug,
  badge,
  title,
  intro,
  tool,
  sections,
  faqs,
  related,
  relatedNote,
}: Props) {
  const canonical = `${BASE}/investor-tools/${slug}`;

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE },
      {
        "@type": "ListItem",
        position: 2,
        name: "Investor Tools",
        item: `${BASE}/investor-tools`,
      },
      { "@type": "ListItem", position: 3, name: title, item: canonical },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />

      {/* Nav */}
      <SiteHeader />

      {/* Header */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-3">
            {badge}
          </Badge>
          <h1 className="font-display text-2xl sm:text-3xl font-semibold text-gold-400 mb-3 tracking-tight italic">
            {title}
          </h1>
          <p className="text-slate-300 max-w-2xl mx-auto leading-relaxed">
            {intro}
          </p>
        </div>
      </section>

      {/* The interactive tool */}
      {tool}

      {/* Explanatory content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-14 mt-6 flex flex-col gap-14 border-t border-slate-800">
        {sections.map((s) => (
          <section key={s.id} id={s.id} className="scroll-mt-20">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              {s.heading}
            </h2>
            <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
              {s.body}
            </div>
          </section>
        ))}

        {related.length > 0 && (
          <section id="related" className="scroll-mt-20">
            <h2 className="text-2xl font-bold text-gold-400 mb-5">
              Related tools
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {related.map((s) => {
                const t = toolBySlug(s);
                if (!t) return null;
                return (
                  <Link
                    key={s}
                    href={t.href}
                    className="glass-card rounded-xl p-5 border border-slate-700 hover:border-gold-400/30 transition-colors"
                  >
                    <h3 className="text-base font-semibold text-slate-100 mb-2">
                      {t.title}
                    </h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      {t.description}
                    </p>
                  </Link>
                );
              })}
            </div>
            {relatedNote && (
              <div className="text-slate-400 mt-6 leading-relaxed">
                {relatedNote}
              </div>
            )}
          </section>
        )}

        {faqs.length > 0 && (
          <section id="faq" className="scroll-mt-20">
            <h2 className="text-2xl font-bold text-gold-400 mb-5">
              Frequently asked questions
            </h2>
            <div className="flex flex-col gap-5">
              {faqs.map((f) => (
                <div key={f.q} className="glass-card rounded-xl p-5">
                  <h3 className="text-base font-semibold text-slate-100 mb-2">
                    {f.q}
                  </h3>
                  <p className="text-slate-300 leading-relaxed">{f.a}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
