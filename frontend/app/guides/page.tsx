import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Mining Investment Guides | Junior Mining Intelligence",
  description:
    "Comprehensive guides for investing in junior mining companies. Learn about gold mining stocks, critical minerals, NI 43-101 reports, and exploration company analysis.",
  keywords: [
    "mining investment guides",
    "junior mining education",
    "gold mining stocks guide",
    "critical minerals guide",
    "mining investment strategies",
  ],
  openGraph: {
    title: "Mining Investment Guides | Junior Mining Intelligence",
    description:
      "Free educational guides for mining investors covering gold, silver, lithium, copper, and critical minerals.",
    type: "website",
    url: "https://juniorminingintelligence.com/guides",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/guides",
  },
};

const guides = [
  {
    title: "How to Read an NI 43-101 Report",
    slug: "how-to-read-ni-43-101-report",
    description:
      "A plain-English guide to skimming a 300-page technical report and extracting the five things that actually matter. Covers resource categories, reserves vs. resources, PEA/PFS/DFS, and 10 red flags that signal a weak report.",
    readTime: "20 min read",
    category: "Technical Analysis",
    featured: true,
  },
  {
    title: "Inferred vs Indicated vs Measured Resources",
    slug: "inferred-vs-indicated-vs-measured-resources",
    description:
      "The three NI 43-101 resource categories explained. What drill spacing produces each, why Inferred can't be used in PFS or DFS, and how to read a category-mixed resource table.",
    readTime: "9 min read",
    category: "Technical Analysis",
    featured: true,
  },
  {
    title: "How to Read Mining Drill Results",
    slug: "how-to-interpret-mining-drill-results",
    description:
      "A plain-English guide to drill press releases. What g/t means, why width matters as much as grade, the press-release tricks that make ordinary intercepts look spectacular, and how to spot real winners.",
    readTime: "18 min read",
    category: "Exploration",
    featured: true,
  },
  {
    title: "The Complete Guide to Junior Gold Mining Companies",
    slug: "junior-gold-mining-companies-guide",
    description:
      "Learn how to evaluate, invest in, and track junior gold mining companies. Covers development stages, risk assessment, NI 43-101 reports, and investment strategies.",
    readTime: "15 min read",
    category: "Gold & Precious Metals",
    featured: true,
  },
  {
    title: "Critical Minerals Investment Guide 2026",
    slug: "critical-minerals-guide",
    description:
      "Comprehensive guide to investing in critical minerals including lithium, copper, rare earths, nickel, cobalt, and graphite. Understand supply chains, demand drivers, and top companies.",
    readTime: "18 min read",
    category: "Critical Minerals",
    featured: true,
  },
];

export default function GuidesPage() {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Link
            href="/"
            className="text-gold-400 hover:text-gold-300 mb-4 inline-block"
          >
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-white">
            Mining Investment Guides
          </h1>
          <p className="text-slate-300 mt-2 text-lg">
            Free educational resources for mining investors
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12">
        {/* Featured Guides */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gold-400 mb-8">
            Featured Guides
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            {guides
              .filter((g) => g.featured)
              .map((guide) => (
                <Link
                  key={guide.slug}
                  href={`/guides/${guide.slug}`}
                  className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 hover:border-gold-500 transition-all hover:shadow-lg hover:shadow-gold-500/10 group"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="bg-gold-500/20 text-gold-400 text-sm px-3 py-1 rounded-full">
                      {guide.category}
                    </span>
                    <span className="text-slate-400 text-sm">
                      {guide.readTime}
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white group-hover:text-gold-400 transition-colors mb-4">
                    {guide.title}
                  </h3>
                  <p className="text-slate-300 leading-relaxed">
                    {guide.description}
                  </p>
                  <div className="mt-6 text-gold-400 font-semibold group-hover:translate-x-2 transition-transform inline-flex items-center">
                    Read Guide →
                  </div>
                </Link>
              ))}
          </div>
        </section>

        {/* Coming Soon */}
        <section>
          <h2 className="text-2xl font-bold text-slate-400 mb-8">
            More Guides Coming Soon
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title:
                  "Gold Grade Explained: g/t, oz/t, ppm, and What's 'High Grade'?",
                category: "Exploration",
              },
              {
                title:
                  "How Junior Mining Companies Get Funded: Private Placements, Flow-Through Shares & Bought Deals",
                category: "Financing",
              },
              {
                title: "Junior Mining Due Diligence: The 12-Point Checklist",
                category: "Investment Strategy",
              },
            ].map((upcoming, idx) => (
              <div
                key={idx}
                className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-6 opacity-60"
              >
                <span className="text-slate-500 text-sm">
                  {upcoming.category}
                </span>
                <h3 className="text-lg font-semibold text-slate-400 mt-2">
                  {upcoming.title}
                </h3>
                <span className="text-slate-500 text-sm mt-4 block">
                  Coming Soon
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mt-16 bg-gradient-to-r from-gold-500/20 to-amber-500/20 border border-gold-500/30 rounded-xl p-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            Start Researching Mining Companies
          </h2>
          <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
            Use our AI-powered platform to analyze over 500 junior mining
            companies, access NI 43-101 reports, and track exploration progress
            in real-time.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/companies"
              className="bg-gold-500 hover:bg-gold-400 text-slate-900 font-bold px-6 py-3 rounded-lg transition-colors"
            >
              Explore Companies
            </Link>
            <Link
              href="/"
              className="bg-slate-700 hover:bg-slate-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              Try AI Chat
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-400">
          <p>© 2026 Junior Mining Intelligence. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
