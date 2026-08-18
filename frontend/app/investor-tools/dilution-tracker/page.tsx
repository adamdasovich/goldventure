import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import DilutionTrackerClient from "./DilutionTrackerClient";

export const revalidate = 3600;

/**
 * Content checked against dilution_tracker in core/views/investor_tools.py:
 * rows are built from the Financing record ordered by announced_date, with
 * cumulative shares issued, total raised, and a count of active warrant
 * tranches. Companies without financing records do not appear in the picker.
 */
export default function DilutionTrackerPage() {
  return (
    <ToolPageLayout
      slug="dilution-tracker"
      badge="Capital Structure"
      title="Dilution Tracker"
      intro="Follow a company's share count through its entire financing history — how many shares each raise issued, what it cost per share, and how much of your ownership has been quietly transferred to later investors."
      tool={<DilutionTrackerClient />}
      related={["warrant-radar", "financing-flow", "resource-growth"]}
      relatedNote={
        <>
          Shares already issued are only part of the story — the{" "}
          <Link
            href="/investor-tools/warrant-radar"
            className="text-gold-400 hover:underline"
          >
            Warrant Overhang Radar
          </Link>{" "}
          shows the shares still queued up. To judge whether the dilution bought
          anything, compare against the{" "}
          <Link
            href="/investor-tools/resource-growth"
            className="text-gold-400 hover:underline"
          >
            Resource Growth Tracker
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
                An exploration company has no revenue. Every drill hole, every
                geologist, every permit application is paid for by issuing new
                shares — which means the ordinary operation of the business
                steadily reduces the fraction of it that existing shareholders
                own.
              </p>
              <p>
                This is not a scandal; it is how the sector works, and a company
                that refuses to raise simply stops exploring. But it is the
                mechanism by which junior mining investors most often lose money
                without the share price ever appearing to collapse. You can be
                right about the deposit, watch the resource grow, and still lose
                because your claim on it shrank faster than it did.
              </p>
              <p>
                This tool lays out the full financing history: every raise, the
                shares issued, the price, and the cumulative effect on the share
                count. It turns a series of individually reasonable
                announcements into the single trend line they add up to.
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
                  Shares issued per raise
                </strong>{" "}
                is the direct dilution from each financing. The important
                comparison is against the share count at the time — ten million
                new shares is trivial against a base of five hundred million and
                severe against a base of twenty million.
              </p>
              <p>
                <strong className="text-slate-100">
                  Cumulative share count
                </strong>{" "}
                is the line that matters most. Watch its shape rather than its
                level. Steady, gentle growth suggests a company raising what it
                needs. A curve that steepens over time suggests one raising
                increasingly often, usually at increasingly poor prices.
              </p>
              <p>
                <strong className="text-slate-100">Price per raise</strong>{" "}
                tells the real story of how the market has received the company.
                Successive financings at progressively lower prices mean each
                round issued more shares for less money — the pattern that
                destroys shareholder value fastest, and the one that compounds,
                because a lower price means more shares next time too.
              </p>
              <p>
                <strong className="text-slate-100">Total capital raised</strong>{" "}
                is the amount consumed to reach the company&apos;s current
                position. Set it against what exists to show for it: ounces
                defined, studies completed, permits obtained.
              </p>
              <p>
                <strong className="text-slate-100">
                  Active warrant tranches
                </strong>{" "}
                flags dilution that has been agreed but not yet occurred.
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
                The question is never whether a company dilutes — it is what the
                dilution bought. The honest test is to compare the growth in
                share count against the growth in whatever the company is
                supposed to be building. If the share count has tripled and the
                resource has grown fivefold, shareholders are ahead on a
                per-share basis. If the share count has tripled and the resource
                has not moved, the money went somewhere other than the ground.
              </p>
              <p>
                Rising financing prices are the strongest signal available here.
                A company raising at progressively higher prices is one the
                market has been rewarding, and it is issuing fewer shares for
                each dollar it needs. That is a virtuous cycle, and it is rare.
              </p>
              <p>
                The pattern to avoid is a steepening share count alongside
                falling raise prices, particularly if it comes with a low{" "}
                <Link
                  href="/investor-tools/signal-to-noise"
                  className="text-gold-400 hover:underline"
                >
                  signal-to-noise ratio
                </Link>
                . That combination describes a company whose main activity is
                funding itself.
              </p>
              <p>
                Timing matters too. Raising into strength, when the share price
                is high, is competent treasury management. Being forced to raise
                into weakness because the treasury ran dry is the expensive
                version, and it tends to happen repeatedly once it starts.
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
                Rows are built from the company&apos;s announced financing
                record, ordered by announcement date, accumulating shares issued
                and capital raised across the sequence and counting warrant
                tranches still outstanding. Only companies with financings on
                record appear.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It covers announced financings, not every source of new
                    shares.
                  </strong>{" "}
                  Shares issued for property acquisitions, to settle debt, or on
                  exercise of options do not appear as financings, so the true
                  share count can grow faster than this history implies.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Warrant exercise is not reflected as it happens.
                  </strong>{" "}
                  Warrants attached to past raises convert into shares over
                  time, often without announcement. The{" "}
                  <Link
                    href="/investor-tools/warrant-radar"
                    className="text-gold-400 hover:underline"
                  >
                    Warrant Overhang Radar
                  </Link>{" "}
                  estimates that pending dilution separately.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Share consolidations distort the history.
                  </strong>{" "}
                  A rollback reduces the share count without returning value to
                  shareholders, and can make a heavily diluted company look
                  restrained.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Coverage depends on announcements being captured.
                  </strong>{" "}
                  Financings are parsed from company releases; anything not
                  published where we can reach it is missing.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "How much dilution is too much for a junior mining company?",
          a: "There is no fixed threshold, because dilution is the cost of exploration rather than a defect. The meaningful test is what it bought: compare growth in share count against growth in the resource, the studies completed, or the permits obtained. A share count that tripled alongside a fivefold resource increase left shareholders better off per share. A share count that tripled with nothing to show did not.",
        },
        {
          q: "Why do junior mining companies dilute so heavily?",
          a: "Because they have no revenue. An exploration company funds drilling, staff and permitting entirely by issuing equity, so every programme is paid for with a slice of the company. Debt is rarely available to a business with no cash flow and no producing asset, which leaves share issuance as the only realistic option.",
        },
        {
          q: "What does a falling financing price across successive raises indicate?",
          a: "That the market has been marking the company down, and that each round is issuing more shares for less money. It is a compounding problem: a lower share price means more shares must be issued next time, which pressures the price further. Successive raises at rising prices indicate the opposite and are much rarer.",
        },
        {
          q: "Does this include dilution from warrants?",
          a: "Not as it occurs. This tool tracks shares issued in announced financings. Warrants attached to those financings convert into shares later, often without a separate announcement, so the Warrant Overhang Radar estimates that pending dilution as a separate exercise.",
        },
        {
          q: "Does a share consolidation reduce dilution?",
          a: "No. A consolidation or rollback reduces the share count proportionally without returning anything to shareholders — your slice of the company is unchanged. It can, however, make a heavily diluted history look restrained, so check whether one has occurred before reading the trend.",
        },
      ]}
    />
  );
}
