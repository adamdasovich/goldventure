import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import CatalystCalendarClient from "./CatalystCalendarClient";

export const revalidate = 3600;

/**
 * The Chrome wrapper added during the soft-404 fix is gone — ToolPageLayout
 * now supplies the nav and header, so the client renders only the calendar.
 */
export default function CatalystCalendarPage() {
  return (
    <ToolPageLayout
      slug="catalyst-calendar"
      badge="Market Intel"
      title="News Catalyst Calendar"
      intro="Track how often junior mining companies actually announce anything — find the most active newsmakers, spot the ones that have gone quiet, and watch weekly news volume across the sector."
      tool={<CatalystCalendarClient />}
      related={["signal-to-noise", "catalyst-impact", "drill-scanner"]}
      relatedNote={
        <>
          Cadence and substance are different things. A company can announce
          constantly and report nothing — the{" "}
          <Link
            href="/investor-tools/signal-to-noise"
            className="text-gold-400 hover:underline"
          >
            Signal-to-Noise Ratio
          </Link>{" "}
          measures which.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Silence is information in junior mining, and it is the kind that
                never arrives in your inbox. A company that stops announcing has
                usually stopped doing — the programme finished, the results were
                not worth publishing, or the treasury emptied — but nothing
                happens to tell you so. You simply notice, eventually, that it
                has been a while.
              </p>
              <p>
                This tool makes that measurable. It tracks announcement
                frequency per company, ranks the most active, and surfaces the
                ones that have gone quiet relative to their own history.
              </p>
              <p>
                It also shows sector-wide news volume over time, which is a
                reasonable proxy for activity levels generally. Drilling
                seasons, financing windows and general enthusiasm all show up in
                how much the sector is talking.
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
                  Release frequency per company
                </strong>{" "}
                is a measure of operational tempo, with an important caveat: it
                counts announcements, not achievements. A promotional company
                will rank highly here.
              </p>
              <p>
                <strong className="text-slate-100">Quiet companies</strong> are
                those whose recent cadence has fallen against their own past.
                This is the more actionable half of the tool. A company that
                published monthly for two years and has said nothing for four
                months has changed, and the change is rarely good.
              </p>
              <p>
                <strong className="text-slate-100">
                  Weekly volume across the sector
                </strong>{" "}
                gives the seasonal backdrop. Northern-hemisphere drilling
                concentrates announcements into particular months, so an
                individual company&apos;s silence during a sector-wide lull is
                far less meaningful than the same silence in a busy period.
              </p>
              <p>
                Always pair frequency with substance. The combination of high
                release count and low signal ratio is the profile of a company
                whose main output is announcements.
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
                Announcement counts are computed from the press releases
                collected for each company over the selected window, aggregated
                by company and by week, with quiet companies identified by
                comparing recent cadence against their longer-run pattern.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It counts announcements, not accomplishments.
                  </strong>{" "}
                  A conference attendance notice counts the same as a resource
                  update. Frequency alone says nothing about whether anything
                  was achieved.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Silence has innocent explanations.
                  </strong>{" "}
                  A company between drill programmes, waiting on assay labs, or
                  in a quiet period before a transaction may legitimately have
                  nothing to say. Turnaround at commercial labs alone can run to
                  months.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Coverage depends on our scraping.
                  </strong>{" "}
                  Releases are collected from company websites daily. A company
                  publishing only through a wire service we do not reach would
                  appear quieter than it is.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Seasonality is not adjusted for.
                  </strong>{" "}
                  Sector-wide volume swings substantially with drilling seasons,
                  so compare a company against the same period a year earlier
                  rather than against the previous quarter.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What does it mean when a junior mining company goes quiet?",
          a: "Most often that the money ran out, the drill programme ended, or the results were not worth announcing. None of those are announced, which is why prolonged silence is worth noticing. There are innocent explanations too — assay lab turnaround can run to months, and companies observe quiet periods around transactions — so treat it as a prompt to check the treasury rather than a conclusion.",
        },
        {
          q: "Does a high announcement count mean a company is doing well?",
          a: "Not on its own. This measures how often a company announces, not what it achieved. A promotional company issuing frequent corporate updates will rank above a working explorer that reports quarterly. Pair the frequency with the Signal-to-Noise Ratio, which measures what share of those announcements report an actual result.",
        },
        {
          q: "How long is too long between announcements?",
          a: "Judge it against the company's own history and the season rather than an absolute threshold. A company that published monthly for two years and has been silent for four months has changed materially. The same four-month gap during a sector-wide winter lull may mean nothing at all.",
        },
        {
          q: "Why does sector news volume rise and fall through the year?",
          a: "Because exploration is seasonal. Much northern-hemisphere drilling happens when ground is accessible, so results cluster in particular months, and financing follows the same rhythm — Canadian flow-through issuance concentrates towards year end for tax reasons. Compare like periods rather than consecutive quarters.",
        },
      ]}
    />
  );
}
