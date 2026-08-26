import Link from "next/link";
import { TOOLS } from "@/app/investor-tools/tools";

/**
 * Contextual "what to do next" block for the guides.
 *
 * The guides are the only pages on this site that reliably rank — they earned
 * ~168 organic sessions in the 30 days to 2026-08-26, while the entire 19-tool
 * suite earned 4 and /open-financings earned 2. The tool pages are not badly
 * built (unique metadata, 1,100+ words each, all in the sitemap); they simply
 * compete for transactional head terms from a young domain, which informational
 * guides win far more easily.
 *
 * So the fix is not more optimisation on the tool pages, it is connecting the
 * pages that rank to the pages that matter — for readers, and for the internal
 * link equity those pages currently do not receive.
 *
 * Tool cards are built from TOOLS in app/investor-tools/tools.ts rather than
 * hand-written per guide, so a retitled or retired tool cannot leave stale
 * marketing copy behind in seven separate 750-line files.
 *
 * Server component on purpose: these links must be in the server-rendered HTML
 * or they do nothing for crawlers.
 */

export interface ExtraLink {
  href: string;
  title: string;
  description: string;
}

interface RelatedResourcesProps {
  /** Tool slugs from tools.ts. Unknown slugs are skipped, not rendered blank. */
  slugs?: string[];
  /** Non-tool destinations — financings, the directory, the weekly report. */
  extra?: ExtraLink[];
  heading?: string;
  /** One line of context. Say why these are worth opening, not that they exist. */
  intro?: string;
}

export function RelatedResources({
  slugs = [],
  extra = [],
  heading = "Put this to work",
  intro,
}: RelatedResourcesProps) {
  const tools = slugs
    .map((slug) => TOOLS.find((t) => t.slug === slug && t.available))
    .filter((t): t is (typeof TOOLS)[number] => Boolean(t));

  const cards: ExtraLink[] = [
    ...tools.map((t) => ({
      href: t.href,
      title: t.title,
      description: t.description,
    })),
    ...extra,
  ];

  if (cards.length === 0) return null;

  return (
    <div className="my-10">
      <h2 className="text-2xl font-bold text-gold-400 mb-3">{heading}</h2>
      {intro && <p className="text-slate-300 mb-6">{intro}</p>}
      <div className="grid md:grid-cols-2 gap-4">
        {cards.map((card, i) => (
          <Link
            key={card.href}
            href={card.href}
            className={`block bg-slate-800 rounded-lg p-5 transition-colors border ${
              i === 0
                ? "border-gold-500/40 hover:border-gold-500"
                : "border-slate-700 hover:border-gold-500/50"
            }`}
          >
            <h3 className="text-lg font-bold text-gold-400 mb-2">
              {card.title}
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              {card.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

/**
 * Shared destinations, so the same phrasing is not reinvented per guide.
 * OPEN_FINANCINGS is the one most guides should carry: it is the most
 * actionable page on the site and had zero inbound links from the four
 * highest-traffic guides.
 */
export const OPEN_FINANCINGS: ExtraLink = {
  href: "/open-financings",
  title: "Open Financings — Participate",
  description:
    "Every junior mining raise currently accepting subscriptions, updated as deals are announced. Register the amount you want through the Participate in Financing flow on the company page, and see how far each round has already filled.",
};

export const CLOSED_FINANCINGS: ExtraLink = {
  href: "/closed-financings",
  title: "Closed Financings Database",
  description:
    "The full history of completed raises — pricing, size and warrant terms deal by deal. How you tell whether a company is raising into strength or grinding its share count higher.",
};

export const COMPANY_DATABASE: ExtraLink = {
  href: "/companies",
  title: "Company Database",
  description:
    "Profiles for 390+ junior miners — projects, resource estimates, drill results, financing history and news, in one searchable place.",
};

export const WEEKLY_REPORT: ExtraLink = {
  href: "/reports/weekly",
  title: "Weekly Mining Report",
  description:
    "Every Friday after the close: top movers with the catalysts behind them, new NI 43-101 reports, financings closed, and the themes emerging across the sector.",
};

export const ALL_TOOLS: ExtraLink = {
  href: "/investor-tools",
  title: "All 19 Investor Tools",
  description:
    "Screeners and analysers built for junior mining — grade ranking, peer comparison, dilution and warrant tracking, drill-result scanning, and portfolio analytics.",
};

export default RelatedResources;
