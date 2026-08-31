import Link from "next/link";

/**
 * Bridge from a financing guide to the financings themselves.
 *
 * /guides/how-junior-mining-companies-raise-money ranks second for "junior
 * mining private placement". It already carried two link blocks to
 * /open-financings, but both sat at lines 1290 and 1420 of a 1,429-line page --
 * past 5,600 words, and only for readers who got that far. This sits directly
 * under the summary box, where someone who has just understood what a placement
 * is is at their most likely to want to see one.
 *
 * Two actions rather than one, because they answer different questions. The
 * first is "what is open right now"; the second is "am I allowed to take part,
 * and how does it work" -- which is the objection that stops most readers, and
 * it is answered on the open-financings page itself.
 *
 * Deliberately not a live deal count. The guide is statically rendered and a
 * data dependency here would add a failure mode to the highest-ranking page on
 * the site in exchange for a number that changes little week to week.
 *
 * Server component: these links have to be in the HTML to pass equity to
 * /open-financings, which is the point of putting them here at all.
 */

interface FinancingCTAProps {
  /** Override the heading where a guide's subject warrants it. */
  heading?: string;
  /** Override the bridging sentence. */
  children?: React.ReactNode;
}

export function FinancingCTA({ heading, children }: FinancingCTAProps) {
  return (
    <aside
      aria-labelledby="financing-cta-heading"
      className="my-12 rounded-lg border border-gold-500/30 border-l-4 border-l-gold-500 bg-slate-800/60 p-6 sm:p-7"
    >
      <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-gold-400/80">
        From reading to doing
      </p>

      <h2
        id="financing-cta-heading"
        className="mb-3 text-xl sm:text-2xl font-bold text-gold-400"
      >
        {heading ?? "See the raises that are open right now"}
      </h2>

      <div className="mb-6 max-w-2xl text-slate-300 leading-relaxed">
        {children ?? (
          <p className="mb-0">
            Everything below explains how these deals are structured. The
            financings themselves are tracked here as they are announced — who
            is raising, at what price, on what structure, and with what warrant
            attached. Most rounds are open for days rather than weeks, so the
            list is only useful while a deal is still live.
          </p>
        )}
      </div>

      {/* Stacks on narrow screens; both targets clear 44px. */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          href="/open-financings"
          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-gold-500 px-5 py-3 font-semibold text-slate-900 transition-colors hover:bg-gold-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold-400"
        >
          Browse open financings
        </Link>
        <Link
          href="/open-financings#how-this-list-works"
          className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-600 px-5 py-3 font-semibold text-slate-200 transition-colors hover:border-gold-500/60 hover:text-gold-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold-400"
        >
          How participation works
        </Link>
      </div>

      <p className="mt-4 mb-0 text-sm text-slate-400">
        Registering interest is not a subscription agreement — it tells the
        company you want an allocation, and you still qualify under the relevant
        exemption before subscribing.
      </p>
    </aside>
  );
}

export default FinancingCTA;
