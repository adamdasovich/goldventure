import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import MetalCorrelationClient from "./MetalCorrelationClient";

export const revalidate = 3600;

/**
 * Content checked against metal_correlation in core/views/investor_tools.py:
 * daily-return correlation, beta = cov(stock, metal) / var(metal), R² =
 * correlation squared, computed on overlapping returns over a configurable
 * window, plus a pairwise correlation matrix for the heatmap.
 */
export default function MetalCorrelationPage() {
  return (
    <ToolPageLayout
      slug="metal-correlation"
      badge="Commodity Leverage"
      title="Metal Leverage Analyzer"
      intro="Measure how closely a mining stock actually tracks its underlying metal, and how much it amplifies the metal's moves — correlation, beta and R² computed from daily returns rather than assumed."
      tool={<MetalCorrelationClient />}
      related={["stock-comparator", "peer-comparison", "unusual-activity"]}
      relatedNote={
        <>
          Leverage to the metal is one reason to own a junior; the deposit is
          the other. Compare the underlying assets with the{" "}
          <Link
            href="/investor-tools/peer-comparison"
            className="text-gold-400 hover:underline"
          >
            Peer Comparison Engine
          </Link>{" "}
          and track the metals themselves on the{" "}
          <Link href="/metals" className="text-gold-400 hover:underline">
            live metals prices page
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
                The standard argument for owning junior miners rather than the
                metal itself is leverage. If gold rises 10%, the reasoning goes,
                a company whose economics depend on the gold price should rise
                considerably more, because the metal price falls almost entirely
                through to margin.
              </p>
              <p>
                It is a sound argument in theory and frequently wrong in
                practice. Plenty of junior mining stocks have their own gravity
                — dilution, disappointing drilling, management turnover, simple
                neglect — that overwhelms whatever the metal is doing. An
                investor buying a gold junior for gold exposure can end up with
                something that barely responds to the gold price at all.
              </p>
              <p>
                This tool checks the assumption. It measures, from actual daily
                price movements, whether a stock moves with its metal and by how
                much — turning &ldquo;this is a leveraged gold play&rdquo; from
                a claim into a number.
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
                <strong className="text-slate-100">Correlation</strong> asks
                whether the stock and the metal move in the same direction, on a
                scale from -1 to 1. Around 0.7 or above is a strong
                relationship; near 0 means the stock is doing its own thing
                regardless of the metal.
              </p>
              <p>
                <strong className="text-slate-100">Beta</strong> asks by how
                much. A beta of 2 means the stock has historically moved roughly
                twice as far as the metal, in both directions. This is the
                number people mean when they say leverage, and it is symmetrical
                — the same amplification that doubles a rally doubles the
                drawdown.
              </p>
              <p>
                <strong className="text-slate-100">R²</strong> is the share of
                the stock&apos;s movement actually explained by the metal. It is
                the correlation squared, so a correlation of 0.7 gives an R² of
                about 0.49 — roughly half the movement explained, the other half
                company-specific.
              </p>
              <p>
                Read beta and R² together, because beta alone is misleading. A
                high beta with a low R² means the stock moves a lot and only
                occasionally because of the metal. That is not leverage; it is
                volatility that happens to be pointed in the right direction
                some of the time.
              </p>
              <p>
                <strong className="text-slate-100">
                  The correlation matrix
                </strong>{" "}
                shows how the selected companies move against each other. If
                every holding in a portfolio correlates tightly, diversification
                across names is not producing diversification of risk.
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
                For an investor deliberately buying metal exposure, the
                attractive profile is a beta comfortably above 1 with an R² high
                enough to show the relationship is real — say 0.4 or better.
                That is a stock genuinely amplifying the metal rather than one
                moving randomly at a larger amplitude.
              </p>
              <p>
                A high beta with a very low R² deserves suspicion. It usually
                describes a volatile microcap whose price swings on drilling,
                financings and speculation, and whose apparent leverage is
                coincidence. You are taking metal risk without reliably getting
                metal exposure.
              </p>
              <p>
                A low beta on a company that should be leveraged is a signal in
                itself. If a gold explorer barely moves when gold moves, the
                market is discounting its ounces heavily — possibly for
                jurisdiction, permitting or dilution reasons worth
                investigating.
              </p>
              <p>
                Remember what beta implies on the way down. A beta of 2.5 is
                attractive in a rising metal market and brutal in a falling one,
                and metal cycles have historically been long enough that the
                falling half arrives.
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
                All three statistics are computed from daily returns — the
                percentage change from one session to the next — for both the
                stock and the metal, using only dates where both have data.
                Correlation is the standard correlation of those two return
                series. Beta is the covariance of stock and metal returns
                divided by the variance of metal returns. R² is the correlation
                squared. The window is adjustable, and the charts show price
                series normalised to a common starting point so paths can be
                compared visually.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    These are historical measurements, not predictions.
                  </strong>{" "}
                  A stock&apos;s beta changes as its story changes. A company
                  that becomes a takeover target or announces a discovery
                  decouples from its metal entirely.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Correlation is not causation.
                  </strong>{" "}
                  A stock can correlate with gold because both respond to
                  interest rates or the dollar, not because the company&apos;s
                  economics depend on the gold price.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Thin trading distorts everything here.
                  </strong>{" "}
                  A stock that does not trade every day has stale prices, which
                  understates correlation and produces unstable beta. Check
                  liquidity before trusting these figures — the{" "}
                  <Link
                    href="/investor-tools/liquidity-screener"
                    className="text-gold-400 hover:underline"
                  >
                    Liquidity screener
                  </Link>{" "}
                  will tell you whether daily prices mean anything for a given
                  name.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Window length changes the answer.
                  </strong>{" "}
                  A short window is dominated by whatever recently happened to
                  the company; a long one averages across periods when the
                  business was materially different. Compare a few windows
                  before concluding anything.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Companies without sufficient price history are excluded
                  </strong>{" "}
                  rather than shown with unreliable statistics.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is a good beta for a junior mining stock?",
          a: "If you are buying the stock for metal exposure, a beta above 1 with a reasonable R² is what you are looking for — it means the stock has historically amplified the metal's moves and that the relationship is genuine. Bear in mind the amplification is symmetrical: a beta of 2.5 doubles-and-a-half the downside as reliably as the upside.",
        },
        {
          q: "What is the difference between correlation and beta?",
          a: "Correlation asks whether two things move together; beta asks by how much. A stock can be highly correlated with gold but barely move when gold does, giving high correlation and low beta. It can also have a high beta driven by a handful of coincidental days, giving high beta and low correlation. You need both numbers to understand the relationship.",
        },
        {
          q: "What does R² tell me that correlation does not?",
          a: "R² is the correlation squared, and it converts the relationship into a share of movement explained. A correlation of 0.7 sounds strong, but the corresponding R² of about 0.49 says only half the stock's movement is attributable to the metal. The rest is company-specific — drilling, financings, management, sentiment.",
        },
        {
          q: "Why does a gold stock sometimes fall when gold rises?",
          a: "Because company-specific events routinely overwhelm the metal. A dilutive financing, a disappointing drill programme, a permitting setback or a management departure can all move a junior far more than a few percent on the gold price. That is exactly what a low R² is measuring.",
        },
        {
          q: "Does thin trading affect these numbers?",
          a: "Considerably. A stock that does not trade every session carries stale closing prices, which understates true correlation and makes beta unstable. For very illiquid names, treat the statistics as indicative at best and check the liquidity screener first.",
        },
      ]}
    />
  );
}
