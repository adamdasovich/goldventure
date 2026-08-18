import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import PeerComparisonClient from "./PeerComparisonClient";

export const revalidate = 3600;

/**
 * Content checked against peer_comparison in core/views/investor_tools.py:
 * peers are auto-detected by the flagship project's primary commodity and the
 * company's exchange; ev_per_oz is market_cap / contained gold oz (NOT true
 * enterprise value) and p_nav is market_cap / (npv_5_usd * 1e6). The EV/oz
 * caveat is stated plainly because the field name implies otherwise.
 */
export default function PeerComparisonPage() {
  return (
    <ToolPageLayout
      slug="peer-comparison"
      badge="Analysis"
      title="Peer Comparison Engine"
      intro="Benchmark a junior mining company against automatically detected peers on market cap per ounce, price to NAV, grade, AISC and financing history — because a valuation only means something relative to something else."
      tool={<PeerComparisonClient />}
      related={["grade-ranker", "resource-growth", "warrant-radar"]}
      relatedNote={
        <>
          A cheap-looking multiple usually has a reason. Check whether the
          resource is genuinely growing with the{" "}
          <Link
            href="/investor-tools/resource-growth"
            className="text-gold-400 hover:underline"
          >
            Resource Growth Tracker
          </Link>
          , and read{" "}
          <Link
            href="/guides/how-to-read-ni-43-101-report"
            className="text-gold-400 hover:underline"
          >
            how to read an NI 43-101 report
          </Link>{" "}
          before trusting an NPV.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                No junior mining company is cheap or expensive in isolation. A
                market capitalisation of $40 million tells you nothing until you
                know what it buys — how many ounces, at what grade, in which
                country, at what stage of development. The only way that figure
                becomes meaningful is alongside companies that are broadly
                comparable.
              </p>
              <p>
                Assembling that comparison by hand is the tedious part of the
                work. It means finding companies with similar deposits, pulling
                resource figures out of technical reports, and normalising
                everything to a per-ounce basis before the numbers can even be
                lined up.
              </p>
              <p>
                This tool does that automatically. Give it a company and it
                identifies a peer group, then lays out the valuation multiples,
                grade, cost figures and financing history side by side — so the
                question becomes why a gap exists rather than whether one does.
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
                  Market cap per contained ounce
                </strong>{" "}
                is what the market is paying for each ounce in the ground. Lower
                looks cheaper, but the number is meaningless without context: an
                inferred ounce in a difficult jurisdiction genuinely should
                trade at a fraction of a permitted ounce in a stable one.
              </p>
              <p>
                <strong className="text-slate-100">P/NAV</strong> compares the
                market capitalisation against the after-tax net present value
                from the company&apos;s own technical study. Below 1.0 means the
                market values the company at less than its study says the
                project is worth. Developers with completed studies commonly
                trade well below 1.0, reflecting the risk that the study&apos;s
                assumptions do not survive contact with reality.
              </p>
              <p>
                <strong className="text-slate-100">Grade</strong> is the
                clearest single indicator of deposit quality, because it drives
                everything downstream — strip ratio, processing cost, and
                whether marginal ounces are economic at a lower metal price.
              </p>
              <p>
                <strong className="text-slate-100">AISC</strong>, all-in
                sustaining cost per ounce, is what it costs to produce an ounce
                including sustaining capital. The gap between AISC and the metal
                price is the margin, and it is what determines survival in a
                downturn.
              </p>
              <p>
                <strong className="text-slate-100">Financing history</strong>{" "}
                shows how much capital each company has consumed to reach its
                current position. Two companies with identical resources but
                very different funding histories are not equivalent.
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
                You are not looking for the lowest multiple. You are looking for
                a gap you can explain — and then for evidence that the
                explanation is wrong.
              </p>
              <p>
                A company trading at half its peer group&apos;s market cap per
                ounce is either mispriced or correctly priced for a reason you
                have not found yet. The reason is usually one of a short list:
                jurisdiction risk, metallurgy that does not work, a resource
                dominated by the inferred category, no route to permitting, a
                capital structure loaded with overhang, or management with a
                history of destroying value. Work through that list before
                concluding the market is wrong.
              </p>
              <p>
                The most reliable use is the opposite direction. When a company
                trades at a large premium to comparable peers, the market is
                pricing in something — usually a discovery, a takeover, or a
                permitting milestone. Identifying what, and judging whether it
                is likely, is often easier than finding a bargain nobody else
                has noticed.
              </p>
              <p>
                Ounces are not fungible. Before drawing conclusions from a
                per-ounce figure, check the resource category split — see{" "}
                <Link
                  href="/guides/inferred-vs-indicated-vs-measured-resources"
                  className="text-gold-400 hover:underline"
                >
                  inferred vs indicated vs measured
                </Link>{" "}
                for why an inferred ounce and a measured ounce should not carry
                the same price.
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
                Peers are detected automatically from the company&apos;s
                flagship project: companies sharing its primary commodity and
                listed on the same exchange. You can override the group and
                specify companies manually, which is worth doing whenever the
                automatic set looks wrong.
              </p>
              <p>
                Resource figures, grades, NPV, IRR and AISC come from filed NI
                43-101 technical reports. Financing totals come from the
                company&apos;s announced raises.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    &ldquo;EV/oz&rdquo; here is market capitalisation per ounce,
                    not true enterprise value per ounce.
                  </strong>{" "}
                  Cash and debt are not netted out. A company holding a large
                  treasury after a recent raise looks more expensive than it is;
                  an indebted one looks cheaper.
                </li>
                <li>
                  <strong className="text-slate-100">
                    P/NAV uses the company&apos;s own NPV.
                  </strong>{" "}
                  That figure comes from its own study, at its own metal price
                  and cost assumptions, and studies are not written by
                  disinterested parties. It is a starting point for
                  investigation, not an independent valuation.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Automatic peer detection is crude.
                  </strong>{" "}
                  Same commodity and same exchange is a reasonable first pass,
                  but it will group an early-stage explorer with a permitted
                  developer, and it takes no account of jurisdiction. Check the
                  group before trusting the comparison.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Contained ounces mix resource categories.
                  </strong>{" "}
                  A per-ounce multiple built largely on inferred material is not
                  comparable to one built on measured and indicated.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Companies without technical reports cannot be scored on
                    every metric.
                  </strong>{" "}
                  Early explorers with no resource estimate will show gaps
                  rather than zeroes.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is a good EV per ounce for a junior mining company?",
          a: "There is no absolute figure, because the range across stages is enormous. An early explorer with an inferred resource in a difficult jurisdiction may trade at a few dollars per ounce, while a permitted developer in a stable one trades at many times that. The number only becomes useful against a peer group at a similar stage — which is what this tool assembles.",
        },
        {
          q: "Is your EV/oz calculated from true enterprise value?",
          a: "No, and this is worth knowing before you use it. The figure is market capitalisation divided by contained ounces; cash and debt are not netted out. A company that has just closed a large financing will therefore look more expensive than a true enterprise value calculation would show, and a company carrying debt will look cheaper.",
        },
        {
          q: "What does a P/NAV below 1.0 mean?",
          a: "That the market is valuing the company at less than the net present value its own technical study assigns to the project. This is common rather than exceptional among developers, because it reflects the real risk that the study's assumptions on metal price, capital cost, permitting and timeline do not hold. A very low P/NAV is a prompt to find out which assumption the market disbelieves.",
        },
        {
          q: "How are peers selected?",
          a: "Automatically, from the flagship project's primary commodity and the company's exchange. It is a reasonable first pass but a blunt one — it takes no account of development stage or jurisdiction, so it may group an early explorer with a permitted developer. You can override the group and choose companies yourself, and it is worth doing whenever the automatic set looks unlike the company you are studying.",
        },
        {
          q: "Why does one company trade at a much lower multiple than its peers?",
          a: "Usually for a reason worth finding before concluding it is mispriced. The common explanations are jurisdiction risk, metallurgy that does not work, a resource weighted towards the inferred category, no clear permitting route, heavy warrant or share overhang, or a management record of dilution. Occasionally the market really has missed something, but that should be the conclusion after checking the list, not before.",
        },
      ]}
    />
  );
}
