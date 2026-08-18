import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import WarrantRadarClient from "./WarrantRadarClient";

export const revalidate = 3600;

/**
 * Content checked against core/views/warrant_radar.py: DEFAULT_WARRANT_COVERAGE
 * = 0.5, the UNITS_TOLERANCE sanity filter, and the module docstring's point
 * that warrant counts are estimates because the coverage fraction is not a
 * field on Financing. That caveat is load-bearing — do not soften it.
 */
export default function WarrantRadarPage() {
  return (
    <ToolPageLayout
      slug="warrant-radar"
      badge="Capital Structure"
      title="Warrant Overhang Radar"
      intro="See every live warrant tranche in the market: the price a stock must reach before warrants become exercisable, the shares that hit the market when they are, the cash that lands in treasury, and when the overhang expires."
      tool={<WarrantRadarClient />}
      related={["dilution-tracker", "financing-flow", "peer-comparison"]}
      relatedNote={
        <>
          Warrants are only half the dilution picture. The{" "}
          <Link
            href="/investor-tools/dilution-tracker"
            className="text-gold-400 hover:underline"
          >
            Dilution Tracker
          </Link>{" "}
          shows the shares already issued, and{" "}
          <Link
            href="/guides/private-placements-and-warrants"
            className="text-gold-400 hover:underline"
          >
            our guide to private placements and warrants
          </Link>{" "}
          explains how the terms are set in the first place.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Junior mining companies fund exploration by issuing units in
                private placements, and a unit is almost always a share plus
                some fraction of a warrant. The warrant is the sweetener: it
                gives the buyer the right to purchase another share later at a
                fixed price. That right is what makes the placement sellable,
                and it is also a liability the company carries for years
                afterwards.
              </p>
              <p>
                The terms sit in individual press releases, one financing at a
                time, and essentially nobody aggregates them. So the question an
                investor actually has — how many shares are queued up to hit the
                market in this stock, at what price, and when — has no
                convenient answer.
              </p>
              <p>
                This tool builds that answer from the financing record: the
                strike prices, the expiry dates, the estimated warrants
                outstanding, the cash that would enter treasury on exercise, and
                the expiry wall showing when large blocks of overhang fall away.
              </p>
            </>
          ),
        },
        {
          id: "how-to-read",
          heading: "How to read the output",
          body: (
            <>
              <p>
                <strong className="text-slate-100">Strike price</strong> is what
                a warrant holder pays to convert their warrant into a share.
                While the market price sits below the strike the warrants are
                out of the money and largely dormant. Above it, exercise becomes
                rational and the overhang becomes real.
              </p>
              <p>
                <strong className="text-slate-100">Percentage to strike</strong>{" "}
                is how far the share price must travel to reach that point. A
                stock trading 5% below a large tranche&apos;s strike has a
                ceiling immediately overhead; one trading 300% below effectively
                does not.
              </p>
              <p>
                <strong className="text-slate-100">
                  Estimated warrants and estimated dilution
                </strong>{" "}
                are the share count that would be created on full exercise, and
                what that represents against the existing count. Both are
                labelled as estimates for a reason explained in the method
                section below.
              </p>
              <p>
                <strong className="text-slate-100">Estimated proceeds</strong>{" "}
                is the cash the company would receive. This is the constructive
                side of warrants: exercise dilutes holders but funds the next
                programme without a new placement, often on better terms than
                the company could otherwise get.
              </p>
              <p>
                <strong className="text-slate-100">The expiry wall</strong>{" "}
                shows when tranches lapse. Warrants that expire unexercised are
                overhang that simply disappears — a quiet, genuinely good
                outcome for existing holders that almost never gets announced.
              </p>
            </>
          ),
        },
        {
          id: "what-good-looks-like",
          heading: "What good looks like",
          body: (
            <>
              <p>
                The situation to understand before buying is a large tranche
                struck slightly above the current price. That is a ceiling. As
                the stock approaches the strike, holders who bought the
                placement have an obvious trade available — exercise and sell —
                and the resulting supply tends to cap the move that triggered
                it. Rallies into a heavy strike frequently stall there for
                reasons that have nothing to do with the geology.
              </p>
              <p>
                The comfortable situation is modest estimated dilution, strikes
                far above the current price, and expiries spread out rather than
                clustered. The uncomfortable one is heavy estimated dilution
                concentrated in a single tranche just overhead.
              </p>
              <p>
                An expiry wall in the near future is worth flagging in both
                directions. If the stock is below the strike, that overhang is
                about to vanish and the share count stops being threatened. If
                it is above, expect exercise and the associated selling before
                the deadline.
              </p>
            </>
          ),
        },
        {
          id: "method",
          heading: "Method and limitations",
          body: (
            <>
              <p>
                Tranches are built from the financing record: units issued,
                warrant strike price, and expiry date, combined with the latest
                available share price. The expiry wall groups tranches by lapse
                date, and the sector-wide view is capped at the largest tranches
                so the payload stays manageable.
              </p>
              <p>
                <strong className="text-slate-100">
                  The most important caveat is that warrant counts are
                  estimates, not facts.
                </strong>{" "}
                Placements are sold as units of one share plus a{" "}
                <em>fraction</em> of a warrant — a half, a third, sometimes a
                whole one. That fraction is stated in the original press release
                but is not recorded as a structured field, so the warrant count
                is derived from an assumed coverage ratio of half a warrant per
                unit, which is the sector norm. The assumption is adjustable. If
                a particular placement was a full-warrant deal, the true
                overhang is roughly double what is shown; if it was a
                third-warrant deal, considerably less.
              </p>
              <p>Everything derived from that count inherits the assumption:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Estimated warrants, dilution and proceeds all scale directly
                    with the coverage ratio.
                  </strong>{" "}
                  Treat them as an order of magnitude for comparing companies,
                  not as a precise figure for one.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Financings whose units look implausible are excluded.
                  </strong>{" "}
                  Units issued should roughly equal the amount raised divided by
                  the price per unit; records disagreeing badly are parse errors
                  rather than exotic deals. One bad row can dominate a
                  sector-wide total, so they are filtered out and counted
                  separately.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Exercised and cancelled warrants may still appear.
                  </strong>{" "}
                  Exercise is not always announced, so a tranche shown as
                  outstanding may have partially converted already. The tool
                  reflects what was issued, not a live registry.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Accelerator clauses are not modelled.
                  </strong>{" "}
                  Many warrants let the company force early exercise if the
                  share price holds above a threshold. Where that applies, the
                  effective expiry can arrive much sooner than the stated date.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is warrant overhang?",
          a: "The pool of shares that could be created if outstanding warrants are exercised. Warrants issued in past financings give holders the right to buy new shares at a fixed strike price. While the share price is below that strike they are mostly dormant; once it rises above, exercise becomes likely, new shares are issued, and existing holders are diluted — often capping the very rally that made exercise attractive.",
        },
        {
          q: "Why are the warrant numbers described as estimates?",
          a: "Because placements are sold as units of one share plus a fraction of a warrant, and that fraction is disclosed in the press release rather than stored as structured data. The tool assumes half a warrant per unit, the sector norm, and lets you change it. A full-warrant placement carries roughly double the overhang shown; a third-warrant placement considerably less.",
        },
        {
          q: "Is warrant exercise bad for shareholders?",
          a: "It cuts both ways. Exercise issues new shares and dilutes existing holders, which is negative. It also puts cash into the treasury without a new placement, which funds the next programme and avoids a raise that might have come at a worse price. The problem is rarely the dilution itself but its timing — exercise clusters exactly when the share price is strong.",
        },
        {
          q: "What does the expiry wall tell me?",
          a: "When large blocks of warrants lapse. If the share price is below the strike as expiry approaches, that overhang disappears and the threat to the share count goes with it — a genuinely good outcome that companies rarely announce. If the price is above the strike, expect a wave of exercise and associated selling ahead of the deadline.",
        },
        {
          q: "Why would a stock stall right below a warrant strike price?",
          a: "Because holders of that tranche have an obvious trade available as the price approaches: exercise at the strike and sell into the strength. That supply arrives precisely when the stock is trying to break higher, which is why a heavy tranche just overhead often functions as a ceiling regardless of the underlying news.",
        },
      ]}
    />
  );
}
