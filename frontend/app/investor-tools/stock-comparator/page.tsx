import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import StockComparatorClient from "./StockComparatorClient";

export const revalidate = 3600;

/**
 * Checked against stock_comparison in core/views/investor_tools.py: up to 10
 * companies, window 7-400 days (default 90), each series normalised to its
 * first day = 0% so curves are comparable regardless of share price.
 */
export default function StockComparatorPage() {
  return (
    <ToolPageLayout
      slug="stock-comparator"
      badge="Analysis"
      title="Stock Performance Comparator"
      intro="Compare the share-price performance of up to ten junior mining companies on one chart, normalised to a common starting point so a three-cent stock and a four-dollar stock can be read against each other."
      tool={<StockComparatorClient />}
      related={["metal-correlation", "peer-comparison", "portfolio-xray"]}
      relatedNote={
        <>
          Relative performance raises the question of why. The{" "}
          <Link
            href="/investor-tools/peer-comparison"
            className="text-gold-400 hover:underline"
          >
            Peer Comparison Engine
          </Link>{" "}
          supplies the valuation and asset data that usually explains it.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Share prices cannot be compared directly. One company trades at
                four cents, another at six dollars, and a chart of the two
                together tells you nothing except which number is larger. What
                matters is the percentage each has moved from a common starting
                point.
              </p>
              <p>
                That is what this does: it rebases every selected company to
                zero on the first day of the window, so the lines show return
                rather than price. Ten companies can then be read against each
                other, and against the period, at a glance.
              </p>
              <p>
                The value is mostly in the divergences. When companies with
                similar assets in similar jurisdictions separate sharply, the
                gap is company-specific — a discovery, a financing, a permitting
                decision, or a market realisation. Finding the date of the
                divergence is usually the fastest route to understanding what
                the market thinks about a name.
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
                <strong className="text-slate-100">
                  The normalised curves
                </strong>{" "}
                all start at zero, so vertical distance between two lines is the
                difference in return over the window, not a difference in price.
              </p>
              <p>
                <strong className="text-slate-100">
                  The point where lines separate
                </strong>{" "}
                matters more than where they end. A gap that opened on a single
                date points at an event; a gap that widened steadily points at a
                gradual repricing, which is often the more durable signal.
              </p>
              <p>
                <strong className="text-slate-100">
                  Your choice of window is an argument.
                </strong>{" "}
                Any comparison can be made to favour a company by choosing when
                it begins. Look at several windows before concluding anything,
                and be suspicious of a single flattering chart — including one
                you produced yourself.
              </p>
              <p>
                <strong className="text-slate-100">Volatility</strong> is
                visible in the shape of each line. Two companies can finish the
                window at the same return having taken very different routes,
                and the smoother one is generally the one with a broader
                shareholder base.
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
                Use it comparatively rather than absolutely. A company up 40%
                over a window when its peer group is up 60% has underperformed,
                and that gap is the thing worth explaining — the sector tide
                lifted everything, and this one lifted less.
              </p>
              <p>
                The most useful setup is a group deliberately chosen to be
                similar: same commodity, same jurisdiction, similar stage. Any
                divergence within a group like that is company-specific by
                construction, which makes it worth investigating. Comparing a
                gold explorer against a lithium developer produces a chart that
                mostly reflects two different commodity cycles.
              </p>
              <p>
                Sustained underperformance against genuine peers usually has a
                cause the market has identified and you have not. Dilution is
                the most common — check the{" "}
                <Link
                  href="/investor-tools/dilution-tracker"
                  className="text-gold-400 hover:underline"
                >
                  Dilution Tracker
                </Link>{" "}
                before concluding a laggard is simply unloved.
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
                Up to ten companies can be charted at once over a window between
                one week and roughly thirteen months, defaulting to 90 days.
                Each series is normalised to its first available day in the
                window as zero percent, and only companies with price history
                appear in the picker.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    The start date determines the story.
                  </strong>{" "}
                  Normalising to day one means every conclusion depends on which
                  day that is. This is the single easiest way to mislead
                  yourself with this tool.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Currency differences are not adjusted.
                  </strong>{" "}
                  Companies listed on different exchanges are compared in their
                  own currencies, so exchange-rate movement is silently included
                  in the relative performance.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Illiquid stocks produce misleading curves.
                  </strong>{" "}
                  A stock that does not trade every day carries stale prices,
                  which flattens its line and understates its real volatility.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Corporate actions are not adjusted for.
                  </strong>{" "}
                  A share consolidation appears as a dramatic price change that
                  reflects no change in value.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Gaps in price history shift the baseline.
                  </strong>{" "}
                  Normalisation uses the first available day, which for a stock
                  with sparse data may not be the window start.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "Why normalise share prices instead of charting them directly?",
          a: "Because absolute prices are not comparable. A company at four cents and one at six dollars produce a chart where the cheaper stock is a flat line at the bottom regardless of how it performed. Rebasing both to zero on day one converts the chart into percentage return, which is the quantity that actually matters to a holder.",
        },
        {
          q: "How do I choose a fair comparison window?",
          a: "Look at several. Any single window embeds an argument, because the starting date determines which company looks best. Checking 90 days, six months and a year together tends to reveal whether a gap is a durable repricing or an artefact of where the chart begins.",
        },
        {
          q: "Which companies should I compare?",
          a: "Ones that are genuinely alike — same commodity, similar jurisdiction, similar development stage. Divergence within a group like that is company-specific by construction and therefore informative. Comparing across commodities mostly charts two different commodity cycles against each other.",
        },
        {
          q: "Does it account for share consolidations?",
          a: "No. A consolidation or rollback appears as a large price change even though shareholder value is unchanged, so a curve spanning one should be treated with caution.",
        },
      ]}
    />
  );
}
