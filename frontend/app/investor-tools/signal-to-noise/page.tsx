import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import SignalToNoiseClient from "./SignalToNoiseClient";

export const revalidate = 3600;

/**
 * Content checked against signal_to_noise in core/views/market_quality.py:
 * HARD_NEWS_TYPES = drill_results, resource_update, study_results, and the
 * minimum release count below which a company is excluded.
 */
export default function SignalToNoisePage() {
  return (
    <ToolPageLayout
      slug="signal-to-noise"
      badge="Market Quality"
      title="Signal-to-Noise Ratio"
      intro="Measure what share of a company's announcements report an actual result — drill intercepts, resource updates, economic studies — rather than corporate housekeeping. It separates the companies exploring from the companies announcing."
      tool={<SignalToNoiseClient />}
      related={["drill-scanner", "catalyst-calendar", "liquidity-screener"]}
      relatedNote={
        <>
          Pair this with the{" "}
          <Link
            href="/investor-tools/catalyst-calendar"
            className="text-gold-400 hover:underline"
          >
            News Catalyst Calendar
          </Link>{" "}
          to separate cadence from substance: a company can be both prolific and
          empty. See also{" "}
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
                Exploration companies communicate constantly. They have to —
                raising money requires visibility, and visibility requires a
                steady flow of announcements. But there is a large difference
                between a company announcing that it has hit twelve metres of
                good grade, and a company announcing that its chief executive
                will be attending a conference in Zurich.
              </p>
              <p>
                Both arrive through the same channel, in the same format, with
                the same air of significance. Read enough of them and the
                distinction blurs, which is precisely the effect a
                promotion-heavy company depends on. A newsfeed that looks busy
                feels like progress.
              </p>
              <p>
                Every release is classified by type, so the distinction can be
                measured rather than sensed. This tool reports, per company,
                what proportion of announcements report a genuine result — and
                compares it against the sector, where only about a quarter of
                junior mining news does.
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
                  The signal percentage
                </strong>{" "}
                is the share of a company&apos;s releases in the window that
                report drill results, a resource update, or study results.
                Everything else — financings, appointments, grants, conference
                attendance, corporate updates — counts as noise. The word is not
                pejorative; these announcements can be necessary. They simply do
                not tell you anything about what is in the ground.
              </p>
              <p>
                <strong className="text-slate-100">
                  The comparison against the sector
                </strong>{" "}
                matters more than the absolute number. Roughly a quarter is
                normal. A company well above that is spending its announcements
                on results; a company well below is spending them on itself.
              </p>
              <p>
                <strong className="text-slate-100">Total release count</strong>{" "}
                is the context that stops the ratio being misread. A company
                with a high percentage across a handful of releases is not
                demonstrating much, which is why very quiet companies are
                excluded entirely.
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
                Above the sector average is the simple reading, but the more
                useful signal is the combination of ratio and volume. A company
                with a high ratio and a healthy number of releases is drilling
                and reporting. A company with a high ratio and very few releases
                is probably doing one programme a year and going quiet in
                between — not necessarily bad, but a different proposition.
              </p>
              <p>
                The pattern that should give pause is a high volume of releases
                with a low signal ratio. That is a company generating attention
                without generating results, and it is the profile of an issuer
                whose primary activity is raising the next round rather than
                spending the last one in the ground.
              </p>
              <p>
                Read the ratio alongside the capital structure. A company
                announcing frequently, reporting little, and steadily issuing
                shares is telling you what it is. The{" "}
                <Link
                  href="/investor-tools/dilution-tracker"
                  className="text-gold-400 hover:underline"
                >
                  Dilution Tracker
                </Link>{" "}
                supplies the other half of that picture.
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
                Every press release we hold is classified by type. Three types
                count as signal — drill results, resource updates, and study
                results — and the ratio is the count of those divided by total
                releases over the window. Companies with fewer than ten releases
                are excluded, because a ratio computed on a handful of items is
                noise itself.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It measures category, not quality.
                  </strong>{" "}
                  A release reporting poor drill results counts exactly the same
                  as one reporting excellent results. High signal means a
                  company is reporting on the ground, not that what it found is
                  good.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Classification is automated and imperfect.
                  </strong>{" "}
                  A release combining a financing announcement with drill
                  results receives a single type, and occasional
                  misclassification is inevitable.
                </li>
                <li>
                  <strong className="text-slate-100">
                    A low ratio is not automatically damning.
                  </strong>{" "}
                  A developer working through permitting has genuinely little
                  drilling to report; its announcements are legitimately
                  corporate. Stage matters, and the ratio is most meaningful
                  between companies at similar stages.
                </li>
                <li>
                  <strong className="text-slate-100">
                    It depends on our news coverage being complete.
                  </strong>{" "}
                  Releases are scraped from company websites daily. A company
                  publishing somewhere we do not reach would be under-counted.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What counts as signal rather than noise?",
          a: "Three categories of announcement count as signal: drill results, resource estimate updates, and study results such as a PEA, pre-feasibility or feasibility study. Everything else counts as noise — financings, management appointments, government grants, conference attendance, and general corporate updates. Noise is not a judgement about whether the announcement mattered, only about whether it told you anything new about the deposit.",
        },
        {
          q: "What is a normal signal-to-noise ratio for a junior mining company?",
          a: "Across the companies we track, only about a quarter of junior mining announcements report an actual result. That makes roughly 25% the sector benchmark, and it is a lower bar than most investors assume before they see the number.",
        },
        {
          q: "Does a high ratio mean the company is a good investment?",
          a: "No. The ratio measures what a company reports on, not what it found. A company diligently publishing consistently disappointing drill results will score well. Treat it as a filter for whether the company is doing exploration work at all, then assess the results themselves.",
        },
        {
          q: "Why are companies with few releases excluded?",
          a: "Because a percentage computed on a very small number of releases is unstable — one announcement either way swings it dramatically. Companies below ten releases in the window are left out rather than shown with a misleadingly precise figure.",
        },
        {
          q: "Can a low signal ratio be legitimate?",
          a: "Yes. A company in permitting or construction has little drilling to report, so its announcements are genuinely corporate. The ratio is most useful when comparing companies at a similar stage — one explorer against another — rather than across the whole sector.",
        },
      ]}
    />
  );
}
