import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import LiquidityScreenerClient from "./LiquidityScreenerClient";

export const revalidate = 3600;

/**
 * Content checked against liquidity_screener in core/views/market_quality.py:
 * LIQUIDITY_LOOKBACK = 60 sessions, PARTICIPATION_RATE = 0.20, and the
 * LIQUIDITY_BANDS thresholds. Do not restate these numbers from memory.
 */
export default function LiquidityScreenerPage() {
  return (
    <ToolPageLayout
      slug="liquidity-screener"
      badge="Market Quality"
      title="Liquidity & Days to Exit"
      intro="Work out how long it would actually take to sell a position in any junior mining stock, using median daily volume and a realistic share of it — the risk that never appears on a conventional screener."
      tool={<LiquidityScreenerClient />}
      related={["signal-to-noise", "unusual-activity", "dilution-tracker"]}
      relatedNote={
        <>
          Liquidity is the first filter, not the last. Once a position is
          tradeable, check whether the company is actually producing results
          with the{" "}
          <Link
            href="/investor-tools/signal-to-noise"
            className="text-gold-400 hover:underline"
          >
            Signal-to-Noise Ratio
          </Link>
          , or browse{" "}
          <Link
            href="/investor-tools"
            className="text-gold-400 hover:underline"
          >
            all investor tools
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
                Almost every piece of junior mining analysis concerns the entry:
                the grade, the jurisdiction, the valuation. Very little concerns
                the exit, and for a sector this thinly traded that is the wrong
                way round. A position you cannot sell at a price you would
                accept is not really an investment; it is a donation with a
                lottery ticket attached.
              </p>
              <p>
                This tool answers one question directly. Given the size of
                position you are considering, and given how much of this stock
                actually changes hands on a normal day, how many trading days
                would it take to get out?
              </p>
              <p>
                The answer is frequently uncomfortable. Across the companies we
                track, the median listing turns over only a few thousand dollars
                a day. At that level, a position most retail investors would
                consider modest takes weeks to unwind — and that is assuming the
                price holds while you do it, which selling pressure of that
                duration tends to prevent.
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
                  Median daily dollar volume
                </strong>{" "}
                is the middle value of the last 60 trading sessions, measured in
                dollars rather than shares so that companies at different share
                prices can be compared. The median is used deliberately: a
                single frenzied day following a drill result would drag an
                average upwards and flatter a stock that is otherwise dormant.
              </p>
              <p>
                <strong className="text-slate-100">Sellable per day</strong> is
                the share of that volume you could realistically take without
                pushing the price against yourself. It is not the whole
                day&apos;s volume, because you are not the only seller and a bid
                that absorbs everything does not exist at these sizes.
              </p>
              <p>
                <strong className="text-slate-100">Days to exit</strong> is your
                position size divided by the sellable-per-day figure. Read it as
                an optimistic floor rather than a forecast: it assumes liquidity
                stays at its recent median, which is exactly what fails during
                the bad news that makes you want to sell.
              </p>
              <p>
                <strong className="text-slate-100">The liquidity band</strong>{" "}
                is a plain-language summary. Under $1,000 of daily turnover a
                listing is treated as untradeable, under $5,000 as very thin,
                under $25,000 as thin, under $100,000 as moderate, and above
                that as liquid. Most junior listings sit in the first two bands.
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
                There is no universal threshold, because the answer depends
                entirely on your position size and your patience. The useful
                discipline is to decide the maximum number of days you would
                tolerate before you look at the number, then size the position
                to fit — rather than choosing a position size first and
                discovering the exit afterwards.
              </p>
              <p>
                As a rough guide, a days-to-exit figure in low single digits is
                comfortable. Anything approaching two weeks means you are the
                market in that stock, and your own selling will set the price
                you receive. Beyond that, treat the position as illiquid by
                nature: size it as money you are prepared to have locked up
                indefinitely, not as a trade you can reverse.
              </p>
              <p>
                One consequence worth internalising: illiquidity is not a
                permanent property of a company, it is a property of its current
                attention. A stock can be untradeable for a year and turn over
                its entire float in the week after a discovery. That cuts both
                ways — the liquidity that lets you in during excitement is
                usually gone by the time you want out.
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
                Median daily dollar volume is computed over the trailing 60
                trading sessions — long enough to survive a quiet fortnight,
                short enough to reflect a stock that has recently woken up.
                Sellable-per-day assumes you can be 20% of a session&apos;s
                volume, the conventional planning figure for thin listings. Days
                to exit is simply your position divided by that figure, and the
                participation rate is adjustable if your own assumption differs.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It measures the recent past, not the future.
                  </strong>{" "}
                  Liquidity is not stable. The 60-session median describes
                  conditions that existed, and those conditions change fastest
                  in precisely the circumstances where the exit matters most.
                </li>
                <li>
                  <strong className="text-slate-100">
                    The 20% participation rate is an assumption, not a
                    measurement.
                  </strong>{" "}
                  It is a widely used planning convention rather than a property
                  of any particular order book. In a genuinely thin name the
                  realistic figure may be lower.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Price impact is not modelled.
                  </strong>{" "}
                  The calculation tells you how long, not at what price. Selling
                  into a thin book moves the price down as you go, so the
                  proceeds are typically worse than the current quote implies.
                </li>
                <li>
                  <strong className="text-slate-100">
                    It depends on market data being present.
                  </strong>{" "}
                  Companies without recent trading history cannot be scored and
                  are excluded rather than shown as liquid.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is a good days-to-exit figure for a junior mining stock?",
          a: "It depends on your position size and how long you are willing to be stuck. Low single-digit days is comfortable. Approaching two weeks means your own selling would set the price you receive. Beyond that the position should be sized as capital you can afford to have locked up indefinitely rather than as a reversible trade.",
        },
        {
          q: "Why measure dollar volume instead of share volume?",
          a: "Because share counts are not comparable across companies. A stock trading at three cents and one trading at four dollars can show wildly different share volumes while the same amount of money changes hands. Dollar volume puts every listing on the same scale, and it is the figure that matters when you are trying to convert a position back into cash.",
        },
        {
          q: "Why use the median rather than the average daily volume?",
          a: "A single exceptional day — the release of a strong drill result, say — would pull an average upwards and make a normally dormant stock look tradeable. The median describes the typical session, which is the condition you will actually be selling into.",
        },
        {
          q: "Does the tool account for the price impact of my selling?",
          a: "No. It tells you how many days, not at what price. Selling into a thin order book pushes the price down as you go, so realised proceeds are usually worse than the current quote suggests. Treat the days figure as an optimistic floor.",
        },
        {
          q: "Why are so many junior mining stocks this illiquid?",
          a: "Because most are small exploration companies with narrow shareholder bases and no institutional following. Trading tends to be concentrated around news, so a listing can go weeks with almost no turnover and then trade heavily for a few days after a result. The long quiet stretches are the normal state, and they are what the median captures.",
        },
      ]}
    />
  );
}
