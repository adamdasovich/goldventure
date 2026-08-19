import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import PortfolioXrayClient from "./PortfolioXrayClient";

export const revalidate = 3600;

/** Checked against portfolio_xray in core/views/investor_tools.py. */
export default function PortfolioXrayPage() {
  return (
    <ToolPageLayout
      slug="portfolio-xray"
      badge="Portfolio"
      title="Portfolio X-Ray"
      intro="Analyse a set of junior mining holdings for what they actually expose you to — commodity concentration, jurisdiction risk and development-stage mix — because a portfolio of ten companies is often one bet held ten times."
      tool={<PortfolioXrayClient />}
      related={["stock-comparator", "liquidity-screener", "metal-correlation"]}
      relatedNote={
        <>
          Concentration is one hidden risk; illiquidity is the other. Run your
          holdings through the{" "}
          <Link
            href="/investor-tools/liquidity-screener"
            className="text-gold-400 hover:underline"
          >
            Liquidity screener
          </Link>{" "}
          to see how much of the portfolio you could actually exit.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Junior mining portfolios accumulate rather than get designed.
                Positions arrive one at a time, each bought for its own reasons,
                and the collection is rarely examined as a whole. The usual
                result is a portfolio that feels diversified because it holds a
                dozen names and is in fact a single concentrated bet.
              </p>
              <p>
                Ten gold explorers in Ontario is not diversification. It is one
                position in the gold price and one position in Ontario
                permitting, split across ten balance sheets — which adds
                company-specific risk without reducing the risk that actually
                dominates the outcome.
              </p>
              <p>
                This tool takes a set of companies and shows what the collection
                exposes you to: which commodities, which jurisdictions, which
                development stages, and how concentrated each of those is.
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
                <strong className="text-slate-100">Commodity exposure</strong>{" "}
                is usually the biggest surprise. Investors who believe they hold
                a spread of metals frequently find 80% of the portfolio sitting
                on one, because gold juniors outnumber everything else and get
                bought one at a time.
              </p>
              <p>
                <strong className="text-slate-100">
                  Geographic concentration
                </strong>{" "}
                is the risk most often underestimated. Jurisdiction determines
                permitting timelines, tax and royalty regimes, and the
                possibility of expropriation. A portfolio concentrated in one
                country is exposed to a single set of political decisions, and
                those decisions arrive without warning.
              </p>
              <p>
                <strong className="text-slate-100">
                  Stage diversification
                </strong>{" "}
                describes the shape of your risk and your timeline. A portfolio
                entirely of grassroots explorers is a series of lottery tickets
                with no near-term cash flow anywhere in it. One entirely of
                developers is exposed to permitting and construction risk in
                unison. A mix spreads both the risk and the timing.
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
                There is no correct allocation, because the right shape depends
                on what you are trying to do. Concentration is a legitimate
                strategy if it is deliberate. The problem this tool addresses is
                concentration you did not know you had.
              </p>
              <p>
                A reasonable target for a portfolio intended to be diversified
                is no single commodity above roughly half, no single
                jurisdiction dominating, and a spread across stages so that not
                everything depends on the same catalyst arriving at the same
                time.
              </p>
              <p>
                The subtler risk is correlated dilution. In a weak market every
                junior needs to raise at once, so a portfolio of pre-revenue
                explorers dilutes in unison exactly when share prices are
                lowest. Holding a company or two with a funded treasury changes
                that dynamic more than adding another explorer does.
              </p>
              <p>
                Worth checking alongside this: whether your holdings actually
                move independently. The{" "}
                <Link
                  href="/investor-tools/metal-correlation"
                  className="text-gold-400 hover:underline"
                >
                  Metal Leverage Analyzer
                </Link>{" "}
                includes a correlation matrix, and tightly correlated holdings
                are not diversifying anything regardless of how the exposure
                chart looks.
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
                You supply a set of companies and the tool aggregates their
                project data — primary commodity, country and development stage
                — alongside market capitalisation, to produce the exposure
                breakdowns.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It does not know your position sizes.
                  </strong>{" "}
                  This is the most important limitation. Exposure is computed
                  across the companies you list, not weighted by what you
                  actually hold, so a token position counts the same as your
                  largest one. Read it as a map of the names, not of your money.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Multi-commodity companies are simplified.
                  </strong>{" "}
                  A company with both copper and gold projects is attributed by
                  its project data rather than split proportionally by value.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Jurisdiction is recorded at country level.
                  </strong>{" "}
                  Provincial and state differences matter enormously for
                  permitting and are not captured.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Correlation is not measured here.
                  </strong>{" "}
                  Companies in different commodities can still move together,
                  and exposure percentages do not reveal that.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "How many junior mining stocks should a portfolio hold?",
          a: "There is no correct number, and the count matters far less than what the holdings expose you to. Ten companies in the same commodity and the same jurisdiction is one concentrated bet held ten ways — it adds company-specific risk without reducing the commodity and political risk that will actually determine the outcome.",
        },
        {
          q: "Why does jurisdiction concentration matter so much in mining?",
          a: "Because a single political decision can reprice every holding at once. Jurisdiction determines permitting timelines, royalty and tax regimes, and in the worst cases the security of tenure itself. A portfolio concentrated in one country is exposed to one government's choices, and those tend to arrive without warning.",
        },
        {
          q: "Does the tool weight by my position sizes?",
          a: "No, and this is worth remembering when reading it. Exposure is computed across the companies you list, treating each equally, so a small speculative position counts the same as a core holding. It maps the names in the portfolio rather than the money in it.",
        },
        {
          q: "What is correlated dilution risk?",
          a: "The tendency for pre-revenue explorers to need financing at the same time. In a weak market every junior's treasury runs low together, so they all raise into the same poor conditions and dilute in unison — precisely when share prices are lowest. Holding companies at different funding stages mitigates this more effectively than simply holding more explorers.",
        },
      ]}
    />
  );
}
