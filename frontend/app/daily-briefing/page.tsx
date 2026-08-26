import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import {
  RelatedResources,
  COMPANY_DATABASE,
  OPEN_FINANCINGS,
  WEEKLY_REPORT,
} from "@/components/guides/RelatedResources";

/**
 * Public page for the Daily Briefing.
 *
 * The feature itself lives on /dashboard, which is personal and correctly kept
 * out of the sitemap — meaning that as of 2026-08-26 nothing describing it
 * existed for search at all. Someone looking for "junior mining watchlist" or
 * "mining stock alerts" had no way to find it.
 *
 * Written as a real explanation rather than a feature brochure, because on this
 * site informational pages are the ones that rank: the guides earned ~168
 * organic sessions in 30 days while the whole 19-tool suite earned 4.
 *
 * Server component — the copy and the internal links must be in the HTML.
 */

const CANONICAL = "https://juniorminingintelligence.com/daily-briefing";

export const metadata: Metadata = {
  title:
    "Daily Briefing — Track Your Junior Mining Watchlist | Junior Mining Intelligence",
  description:
    "A daily briefing on the junior miners you follow: price moves with the news behind them, financings, and new NI 43-101 documents. Build a watchlist and see what changed while you were away.",
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: "Daily Briefing — Track Your Junior Mining Watchlist",
    description:
      "Price moves with the news behind them, financings, and new technical reports — for the juniors you actually follow.",
    type: "website",
    url: CANONICAL,
  },
};

export default function DailyBriefingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader active="/daily-briefing" />

      <section className="relative py-12 sm:py-16 lg:py-20 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50" />
        <div className="relative max-w-4xl mx-auto">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-5 text-gradient-gold leading-tight text-balance pb-1">
            Your Daily Briefing on the Juniors You Follow
          </h1>
          <p className="text-lg text-slate-300 leading-relaxed">
            Following junior miners is mostly a problem of attention. There are
            more than five hundred of them, they release news at all hours, and
            most of what they publish does not matter. The briefing is the
            opposite of a news feed: it watches only the companies you have
            chosen, and it tells you what changed.
          </p>
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <article className="max-w-4xl mx-auto prose-invert">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            What it tells you
          </h2>
          <p className="text-slate-300 leading-relaxed mb-4">
            Each briefing covers your watchlist over a rolling window and leads
            with a generated headline — the single thing most worth knowing
            before you read further. Underneath it:
          </p>

          <dl className="space-y-5 mb-10">
            <div>
              <dt className="font-semibold text-white">
                Price moves, with the news attached
              </dt>
              <dd className="mt-1 text-slate-400 leading-relaxed">
                Not just that a holding moved, but what was published around the
                time it moved. A move on an assay result and a move on nothing
                are different facts, and only one of them needs your attention.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-white">
                Financings involving your companies
              </dt>
              <dd className="mt-1 text-slate-400 leading-relaxed">
                When a company you hold raises capital, it changes both the
                balance sheet and your position. The briefing surfaces it rather
                than leaving you to notice the dilution later.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-white">
                New technical documents
              </dt>
              <dd className="mt-1 text-slate-400 leading-relaxed">
                NI 43-101 reports, PEAs and feasibility studies filed by your
                companies — the documents that move a project between stages and
                usually reprice it.
              </dd>
            </div>
          </dl>

          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            Why a watchlist rather than a feed
          </h2>
          <p className="text-slate-300 leading-relaxed mb-4">
            A sector-wide feed of junior mining news is close to unreadable.
            Hundreds of companies publish routine filings, and the few releases
            that genuinely reprice a stock are buried among them. Narrowing to
            the companies you have actually researched changes the ratio
            entirely — and it means the absence of news is informative too.
          </p>
          <p className="text-slate-300 leading-relaxed mb-10">
            You build the watchlist from the{" "}
            <Link
              href="/companies"
              className="text-gold-400 hover:underline font-medium"
            >
              company database
            </Link>
            , adding juniors as you research them. The briefing then follows
            whatever is on it. There is also a weekly email version if you would
            rather it came to you.
          </p>

          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            How it differs from the weekly report
          </h2>
          <p className="text-slate-300 leading-relaxed mb-10">
            The{" "}
            <Link
              href="/reports/weekly"
              className="text-gold-400 hover:underline font-medium"
            >
              weekly mining report
            </Link>{" "}
            covers the whole sector — every junior, every material release,
            every financing closed that week. It is how you find companies you
            did not know about. The daily briefing is the reverse: it ignores
            the sector and watches your holdings. Most investors want both, for
            different reasons.
          </p>

          <RelatedResources
            heading="Start here"
            intro="Build a watchlist first — the briefing has nothing to report until it knows which companies you follow."
            slugs={["portfolio-xray", "dilution-tracker", "catalyst-calendar"]}
            extra={[COMPANY_DATABASE, OPEN_FINANCINGS, WEEKLY_REPORT]}
          />
        </article>
      </section>
    </div>
  );
}
