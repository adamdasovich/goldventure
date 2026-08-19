import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import CatalystImpactClient from "./CatalystImpactClient";

export const revalidate = 3600;

/**
 * Checked against catalyst_impact in core/views/investor_tools.py: an event
 * study measuring price reaction at 1, 5 and 20 TRADING days after each
 * release, grouped by news type, over a 90-1095 day window (default 365).
 */
export default function CatalystImpactPage() {
  return (
    <ToolPageLayout
      slug="catalyst-impact"
      badge="Event Study"
      title="Catalyst Impact Analyzer"
      intro="See how a company's share price has historically reacted to each type of announcement — drill results, financings, resource updates — measured at one, five and twenty trading days after the release."
      tool={<CatalystImpactClient />}
      related={["unusual-activity", "catalyst-calendar", "signal-to-noise"]}
      relatedNote={
        <>
          Historical reaction is one input; whether the company produces
          catalysts at all is another. Check its cadence with the{" "}
          <Link
            href="/investor-tools/catalyst-calendar"
            className="text-gold-400 hover:underline"
          >
            News Catalyst Calendar
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
                Junior mining investors spend a great deal of energy
                anticipating catalysts — the drill result, the resource update,
                the study — on the assumption that a good one will move the
                share price. The assumption is rarely tested against the
                company&apos;s own history.
              </p>
              <p>
                It should be, because the answer varies enormously between
                companies. Some stocks reliably move on drill results and ignore
                everything else. Some barely respond to anything, because the
                shareholder base is inattentive or the float is too tight to
                trade. Some sell off on any announcement at all, which usually
                means the market expects every release to be followed by a
                financing.
              </p>
              <p>
                This is an event study. For each type of announcement, it
                measures what the share price actually did afterwards across the
                company&apos;s own history — turning &ldquo;drill results should
                move this stock&rdquo; into a measured average.
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
                <strong className="text-slate-100">By catalyst type</strong> is
                the core of it: average price reaction grouped by the kind of
                announcement. The comparison between types is what matters — a
                company whose drill results move the price 8% while financings
                move it -4% is telling you how its shareholders think.
              </p>
              <p>
                <strong className="text-slate-100">
                  One, five and twenty trading days
                </strong>{" "}
                capture different things. The one-day figure is the immediate
                reaction, which on an illiquid stock can be an artefact of a
                single trade. Five days shows whether the move held once the
                initial excitement passed. Twenty days shows whether it was a
                genuine repricing or a spike that faded.
              </p>
              <p>
                The relationship between the three is often more informative
                than any one. A large one-day move that has entirely decayed by
                day twenty describes a stock that gets traded on news rather
                than held on it.
              </p>
              <p>
                <strong className="text-slate-100">Sample size</strong> governs
                how much weight any of this deserves. An average drawn from
                three events is an anecdote.
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
                The encouraging profile is a positive and durable response to
                exploration results — a move at day one that is still largely
                intact at day twenty. That describes a shareholder base paying
                attention to the geology and repricing the company when the
                asset improves.
              </p>
              <p>
                A negative average response to financings is normal rather than
                alarming; dilution is genuinely bad news for existing holders.
                What matters is the magnitude. A stock that falls heavily on
                every raise has a shareholder base that fears dilution more than
                it values the exploration the money funds, which makes each
                subsequent raise more expensive.
              </p>
              <p>
                Muted responses across every category are the least attractive
                pattern. A company whose share price does not respond to good
                news has an audience problem, and no amount of drilling fixes it
                until someone is watching. That is often a liquidity condition
                rather than a company one.
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
                Each classified press release is matched to the company&apos;s
                price history, and the return is measured from the release date
                to one, five and twenty <em>trading</em> days afterwards — not
                calendar days, so weekends and holidays do not distort the
                windows. Results are averaged by announcement type over a window
                of between 90 days and three years, defaulting to one year.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Small samples dominate the averages.
                  </strong>{" "}
                  Most juniors publish few releases of any given type in a year,
                  so a single dramatic event can define the average for that
                  category. Always read the count alongside the number.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Market-wide moves are not stripped out.
                  </strong>{" "}
                  A drill result published on a day the whole gold sector
                  rallied will show a strong reaction that had little to do with
                  the drilling. There is no adjustment for sector or index
                  movement.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Announcement type does not capture whether the news was
                    good.
                  </strong>{" "}
                  Excellent and disappointing drill results are averaged
                  together, so a weak average may mean poor results rather than
                  an inattentive market.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Past reaction does not predict future reaction.
                  </strong>{" "}
                  Shareholder bases change, and a stock that ignored news for
                  two years can reprice violently once it is discovered.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Thin trading distorts short windows.
                  </strong>{" "}
                  On an illiquid stock the one-day figure may reflect a single
                  small trade rather than a market judgement.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is an event study?",
          a: "A method for measuring how an asset's price reacts to a particular category of event, by looking at returns over fixed windows following each occurrence and averaging across them. Here the events are press releases grouped by type, and the windows are one, five and twenty trading days after publication.",
        },
        {
          q: "Why measure at one, five and twenty days rather than just one?",
          a: "Because they answer different questions. One day captures the immediate reaction, which on a thin stock can be a single trade. Five days shows whether the move survived the initial excitement. Twenty days shows whether the market genuinely repriced the company or simply traded around the announcement before drifting back.",
        },
        {
          q: "Why does my company show a negative reaction to financings?",
          a: "Because financings dilute existing shareholders, and that is legitimately bad news for them. A modest negative reaction is normal. A large one indicates a shareholder base that fears dilution more than it values the exploration being funded — which tends to make each subsequent raise more expensive.",
        },
        {
          q: "Can I use this to predict how the next announcement will be received?",
          a: "Only loosely. It describes how this shareholder base has behaved, which is genuine information, but shareholder bases change and samples are small. A stock that ignored news for two years can reprice sharply once it attracts attention. Treat it as a description of the past rather than a forecast.",
        },
        {
          q: "Does it separate good drill results from bad ones?",
          a: "No. Announcements are grouped by type, not by whether the content was favourable. A weak average reaction to drill results may mean the market is inattentive, or it may simply mean the results have been disappointing. The tool cannot tell you which.",
        },
      ]}
    />
  );
}
