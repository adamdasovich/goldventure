import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import UnusualActivityClient from "./UnusualActivityClient";

export const revalidate = 3600;

/**
 * Checked against unusual_activity in core/views/investor_tools.py: trailing
 * 20 trading days for the volume baseline, window 30-365 days (default 90),
 * volume multiple 1.5-10 (default 2.5), news cross-referenced by date.
 */
export default function UnusualActivityPage() {
  return (
    <ToolPageLayout
      slug="unusual-activity"
      badge="Market Intel"
      title="Unusual Activity Detector"
      intro="Find days when a stock traded far above its recent normal volume, and check whether news explains the move — separating announced events from accumulation nobody announced."
      tool={<UnusualActivityClient />}
      related={["catalyst-impact", "drill-scanner", "liquidity-screener"]}
      relatedNote={
        <>
          A spike tells you something happened; the{" "}
          <Link
            href="/investor-tools/catalyst-impact"
            className="text-gold-400 hover:underline"
          >
            Catalyst Impact Analyzer
          </Link>{" "}
          tells you how that category of event has historically played out.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Volume is the least ambiguous signal a thinly traded stock
                produces. Price can drift on a handful of shares and tell you
                almost nothing. A sudden multiple of normal turnover means
                somebody with conviction is transacting, and in a market where
                most listings trade a few thousand dollars a day, that is
                unusual enough to be worth examining.
              </p>
              <p>
                The interesting cases are the unexplained ones. When volume
                spikes on the morning of a drill result, the market is doing
                what it should. When volume spikes on a quiet Tuesday with no
                announcement, something else is happening — accumulation ahead
                of news, a holder exiting, or a position being built by someone
                who has done work you have not.
              </p>
              <p>
                This tool flags days where volume exceeded its recent baseline
                by a chosen multiple, and cross-references the news record so
                explained and unexplained spikes can be told apart.
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
                <strong className="text-slate-100">Flagged days</strong> are
                sessions where volume exceeded the trailing baseline by your
                chosen multiple. The default of two and a half times normal is a
                reasonable starting point; lowering it surfaces more noise,
                raising it isolates only dramatic events.
              </p>
              <p>
                <strong className="text-slate-100">
                  The news cross-reference
                </strong>{" "}
                is the important column. A flagged day matched to an
                announcement is the market reacting, which is informative but
                not surprising. A flagged day with nothing attached is the
                signal worth investigating.
              </p>
              <p>
                <strong className="text-slate-100">
                  Price movement alongside volume
                </strong>{" "}
                changes the interpretation entirely. Heavy volume with the price
                up suggests buying pressure; heavy volume with the price down
                suggests a seller working through the book. Heavy volume with
                the price flat often means a block changed hands between two
                parties who already agreed on value.
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
                The pattern most worth noticing is a cluster of unexplained
                volume days with the price grinding higher and no news. In a
                sector where information leaks — drill crews, assay labs,
                contractors and their families all see results before the market
                does — persistent accumulation before an announcement is a real
                phenomenon rather than a conspiracy theory.
              </p>
              <p>
                Equally informative is the opposite: a major announcement that
                produces no volume response. If a company reports what it calls
                a significant intercept and the market barely trades, the market
                has judged it insignificant. That disagreement is worth
                understanding before you side with the press release.
              </p>
              <p>
                Be careful with single spikes on very illiquid names. In a stock
                that normally trades almost nothing, one ordinary retail order
                can produce a tenfold volume multiple that means nothing at all.
                Check the absolute dollar volume, not just the multiple — the{" "}
                <Link
                  href="/investor-tools/liquidity-screener"
                  className="text-gold-400 hover:underline"
                >
                  liquidity screener
                </Link>{" "}
                gives you the baseline.
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
                The baseline is the average volume over the trailing 20 trading
                days. Any session exceeding that baseline by the chosen multiple
                is flagged. The lookback window is adjustable between 30 and 365
                days, and the multiple between 1.5 and 10. News releases are
                matched to flagged days by date, and price history is
                over-fetched beyond the window so that the earliest days still
                have a full baseline behind them.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Multiples are unreliable on very thin stocks.
                  </strong>{" "}
                  When normal volume is near zero, any trade at all produces a
                  large multiple. Always sanity-check the absolute dollar value
                  of the flagged session.
                </li>
                <li>
                  <strong className="text-slate-100">
                    News matching is by date, not by content.
                  </strong>{" "}
                  A spike on a day with an unrelated announcement will appear
                  explained when it is not, and news published after the close
                  attaches to the wrong session.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Index and fund rebalancing is not identified.
                  </strong>{" "}
                  Some unexplained spikes are mechanical — a fund entering or
                  leaving a position for reasons unconnected to the company.
                </li>
                <li>
                  <strong className="text-slate-100">
                    A 20-day baseline adapts to recent conditions.
                  </strong>{" "}
                  After a sustained period of heavy trading the baseline rises,
                  so continued high volume stops being flagged.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What does unusual trading volume in a mining stock mean?",
          a: "That someone is transacting with more conviction than usual. In a sector where most listings trade very little on a normal day, a large multiple of baseline volume means real orders are being worked. Whether that is informed buying, a holder exiting, or a mechanical fund trade is what the news cross-reference and price direction help you judge.",
        },
        {
          q: "Is unexplained volume a reliable buy signal?",
          a: "No, and it should not be treated as one. It is a prompt to look harder at a company, not a conclusion. Unexplained volume can be accumulation ahead of news, but it can equally be a fund rebalancing, a private block trade, or an estate liquidating a position. The tool tells you where to look, not what you have found.",
        },
        {
          q: "Why does a volume spike sometimes mean nothing on a small stock?",
          a: "Because the multiple is relative. If a listing normally trades a few hundred dollars a day, a single ordinary retail order can be ten times the baseline while being financially trivial. Always check the absolute dollar volume of the flagged session before drawing any conclusion.",
        },
        {
          q: "What does high volume with no price movement indicate?",
          a: "Usually a block trade — a large holding changing hands between two parties who have already agreed a price. It shows a significant position moved without telling you much about direction, though who was buying and why can be worth investigating.",
        },
        {
          q: "What multiple should I set?",
          a: "The default of 2.5 times the trailing 20-day baseline is a sensible starting point. Lower it to around 1.5 and you will see far more sessions, most of them noise. Raise it towards 5 and only dramatic events survive, which is useful on a liquid name and will show almost nothing on a quiet one.",
        },
      ]}
    />
  );
}
