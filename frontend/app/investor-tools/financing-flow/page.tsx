import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import FinancingFlowClient from "./FinancingFlowClient";

export const revalidate = 3600;

/** Checked against financing_flow in core/views/investor_tools.py. */
export default function FinancingFlowPage() {
  return (
    <ToolPageLayout
      slug="financing-flow"
      badge="Market Intel"
      title="Financing Flow Tracker"
      intro="Follow where capital is actually entering junior mining — by month, by commodity and by financing type — because money moves into a theme before prices do."
      tool={<FinancingFlowClient />}
      related={["warrant-radar", "dilution-tracker", "sector-pulse"]}
      relatedNote={
        <>
          For the individual deals rather than the aggregate, see{" "}
          <Link
            href="/open-financings"
            className="text-gold-400 hover:underline"
          >
            open financings
          </Link>{" "}
          and the{" "}
          <Link
            href="/reports/financings"
            className="text-gold-400 hover:underline"
          >
            weekly financing roundup
          </Link>
          .
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Junior mining runs on raised capital. Nothing happens without
                it: no drilling, no studies, no permitting. That makes financing
                activity the sector&apos;s most direct measure of health, and it
                leads the things investors usually watch.
              </p>
              <p>
                It leads them because raising money requires someone to write a
                cheque, and the people writing cheques into placements are
                generally better informed than the retail market. When capital
                starts flowing into a commodity that was ignored six months
                earlier, the drilling that money pays for arrives a year later,
                and the results a year after that.
              </p>
              <p>
                This tool aggregates announced financings into monthly totals,
                broken down by commodity and by the type of instrument used, so
                that shift is visible while it is happening rather than in
                hindsight.
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
                <strong className="text-slate-100">Monthly totals</strong> show
                the sector&apos;s overall funding conditions. Rising totals mean
                capital is available and companies are taking it; falling totals
                mean the window is closing, which is when treasuries start
                running down and quality companies get forced into bad raises.
              </p>
              <p>
                <strong className="text-slate-100">By commodity</strong> is
                where the rotation shows. The absolute leader is usually gold
                simply because there are more gold juniors than anything else,
                so watch the direction of change rather than the ranking. A
                commodity whose share of financing has doubled is where
                attention is moving.
              </p>
              <p>
                <strong className="text-slate-100">By financing type</strong>{" "}
                describes the terms companies are able to get. A market skewed
                towards flow-through and straight equity is a healthy one. A
                shift towards convertible instruments and heavily
                warrant-sweetened units signals that companies are having to pay
                more for the same money.
              </p>
              <p>
                <strong className="text-slate-100">
                  Deal count against total value
                </strong>{" "}
                separates two different markets. Many small raises describe a
                broad, healthy sector; a few very large ones describe capital
                concentrating into a handful of favoured names while everyone
                else goes hungry.
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
                A healthy sector shows steady or rising monthly totals spread
                across a reasonable number of deals, with terms that are not
                deteriorating. That is a market where a good company with a real
                project can fund itself without giving away the upside.
              </p>
              <p>
                The most actionable signal is a commodity whose share of
                financing is rising from a low base. Capital rotating into a
                previously ignored metal has repeatedly preceded the exploration
                cycle in that metal, and the companies raising early tend to be
                the ones with the ground already staked.
              </p>
              <p>
                Falling totals with a shift towards expensive instruments is the
                warning pattern. In that environment, check the treasury
                position of anything you hold — a company that must raise into a
                closed window will do so at whatever price it can get, and the{" "}
                <Link
                  href="/investor-tools/dilution-tracker"
                  className="text-gold-400 hover:underline"
                >
                  Dilution Tracker
                </Link>{" "}
                shows how much damage previous forced raises have already done.
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
                Announced financings are grouped into monthly buckets across the
                selected window, which is specified in months and measured back
                from today. Commodity attribution comes from the raising
                company&apos;s projects rather than from the financing itself,
                and financing type comes from the announcement.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Announced is not closed.
                  </strong>{" "}
                  Financings are recorded when announced. Deals that are later
                  downsized, upsized or abandoned may not be revised, so totals
                  reflect intent more than settled capital.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Commodity attribution is by company, not by use of funds.
                  </strong>{" "}
                  A company with both gold and copper projects is attributed by
                  its project data, regardless of which project the money is
                  actually destined for.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Coverage depends on announcements being captured.
                  </strong>{" "}
                  Financings are parsed from company releases, so anything
                  published where we do not reach is missing and totals are a
                  floor rather than a complete market figure.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Monthly buckets are approximate.
                  </strong>{" "}
                  The window is computed in 30-day units rather than calendar
                  months, so bucket edges drift slightly from month boundaries.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Seasonality is real and unadjusted.
                  </strong>{" "}
                  Financing activity follows drilling seasons and tax deadlines,
                  particularly for flow-through issues in Canada, so
                  month-on-month comparisons can mislead. Compare with the same
                  period a year earlier.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "Why does financing activity lead the junior mining cycle?",
          a: "Because capital has to arrive before anything can happen. Money raised today funds drilling next season and results the season after. The people funding placements are also generally better informed than the retail market, so a shift in where capital flows tends to precede the shift in sentiment and price.",
        },
        {
          q: "What does a rise in warrant-heavy financings indicate?",
          a: "That companies are paying more for the same money. Warrant coverage is the sweetener that makes a placement sellable, so heavier coverage and more convertible structures mean investors are demanding better terms — a sign that the financing window is tightening even if headline totals have not yet fallen.",
        },
        {
          q: "Does this show every financing in the sector?",
          a: "No. Financings are parsed from company announcements we collect, so the totals are a floor rather than a complete market figure. They are most useful as a trend across months and commodities rather than as an absolute measure of capital raised.",
        },
        {
          q: "Why compare year on year rather than month to month?",
          a: "Because financing is strongly seasonal. Activity follows drilling seasons and, in Canada, the tax deadlines that drive flow-through issuance late in the year. A month-on-month fall may be entirely seasonal, so the same month a year earlier is the more meaningful comparison.",
        },
      ]}
    />
  );
}
