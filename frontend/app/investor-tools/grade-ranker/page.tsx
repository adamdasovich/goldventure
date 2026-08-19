import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import GradeRankerClient from "./GradeRankerClient";

export const revalidate = 3600;

/** Checked against grade_ranker in core/views/investor_tools.py. */
export default function GradeRankerPage() {
  return (
    <ToolPageLayout
      slug="grade-ranker"
      badge="Screener"
      title="Resource Grade Ranker"
      intro="Rank junior mining companies by the grade and size of their mineral resource, filtered by commodity and development stage — the fastest way to see which deposits are actually high grade rather than merely described that way."
      tool={<GradeRankerClient />}
      related={["peer-comparison", "resource-growth", "drill-scanner"]}
      relatedNote={
        <>
          Grade is the starting point, not the conclusion. Check what the market
          is paying for those ounces with the{" "}
          <Link
            href="/investor-tools/peer-comparison"
            className="text-gold-400 hover:underline"
          >
            Peer Comparison Engine
          </Link>
          , and read{" "}
          <Link
            href="/guides/gold-grade-explained"
            className="text-gold-400 hover:underline"
          >
            gold grade explained
          </Link>{" "}
          for what the numbers mean.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Almost every junior mining company describes its deposit as high
                grade. The word has no fixed definition, it costs nothing to
                use, and in a press release it is doing marketing work rather
                than geological work.
              </p>
              <p>
                Grade is nonetheless the single most important property of a
                deposit, because it drives everything downstream. Higher grade
                means less rock moved and processed per ounce recovered, which
                means lower costs, better margins, and survival when the metal
                price falls. Two deposits with identical ounce counts can have
                completely different economics depending on the grade those
                ounces sit at.
              </p>
              <p>
                This tool ranks companies by the grade and size of their
                reported resource, so &ldquo;high grade&rdquo; becomes a
                position in a list rather than an adjective. Filter by
                commodity, development stage and minimum resource size, and sort
                by grade or contained ounces.
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
                <strong className="text-slate-100">Grade</strong> is reported in
                the units conventional for the metal — grams per tonne for gold
                and silver, percentages for base metals. Sorting by grade alone
                will surface small, very rich deposits that may be too small to
                mine economically.
              </p>
              <p>
                <strong className="text-slate-100">Contained ounces</strong> is
                the size of the prize. A very high grade on a tiny resource is a
                geological curiosity; the combination of decent grade and
                meaningful scale is what supports a mine.
              </p>
              <p>
                <strong className="text-slate-100">Tonnage</strong> is what
                connects the two, since ounces are grade multiplied by tonnage.
                It also indicates the mining method implied: large tonnage at
                low grade suggests open pit, small tonnage at high grade
                suggests underground, and the capital requirements differ
                enormously.
              </p>
              <p>
                <strong className="text-slate-100">Stage</strong> tells you how
                far the project has travelled. An exploration-stage resource and
                a feasibility-stage one are not comparable propositions even at
                identical grade, because one has been tested against real costs
                and the other has not.
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
                Useful grade thresholds depend entirely on the deposit type. For
                gold, an open-pit operation can work below 1 g/t if the tonnage
                and strip ratio cooperate, while an underground mine generally
                needs several grams per tonne to justify the development cost.
                Anything sustained above roughly 5 g/t is genuinely high grade;
                the handful of deposits above 10 g/t are exceptional.
              </p>
              <p>
                What you are looking for is not the top of the grade list but
                the combination that is out of step with its valuation — decent
                grade, meaningful scale, a sensible jurisdiction, and a market
                capitalisation that has not caught up. The top of a pure grade
                sort is usually occupied by tiny high-grade resources that
                cannot support a mine.
              </p>
              <p>
                Watch the resource category as well as the number. A headline
                grade computed largely from inferred material carries far less
                confidence than the same grade in the measured and indicated
                categories — see{" "}
                <Link
                  href="/guides/inferred-vs-indicated-vs-measured-resources"
                  className="text-gold-400 hover:underline"
                >
                  inferred vs indicated vs measured
                </Link>
                .
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
                Rankings are built from resource estimates in filed NI 43-101
                technical reports, taking the most recent estimate for each
                project and preferring measured and indicated categories where
                available. Filters apply to the project&apos;s primary
                commodity, its development stage, and a minimum contained-ounce
                threshold.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Grade is not comparable across deposit types.
                  </strong>{" "}
                  An open-pit heap-leach operation and a narrow-vein underground
                  mine have entirely different economic thresholds, and ranking
                  them in one list flatters the second.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Metallurgy is not captured.
                  </strong>{" "}
                  A high-grade deposit whose ore is refractory, or which carries
                  penalty elements, can be worth less than a lower-grade one
                  that processes cleanly. Grade says nothing about recovery.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Only companies with filed resource estimates appear.
                  </strong>{" "}
                  Early-stage explorers with promising drilling but no formal
                  estimate are absent entirely, which is not a judgement on
                  them.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Resource categories are mixed.
                  </strong>{" "}
                  Figures may combine measured, indicated and inferred material
                  of quite different confidence.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is considered a high grade for a gold deposit?",
          a: "It depends on mining method. Open-pit operations can be economic below 1 g/t where tonnage and strip ratio allow, while underground mines generally need several grams per tonne to justify development costs. As orientation, sustained grades above about 5 g/t are genuinely high grade and above 10 g/t is exceptional.",
        },
        {
          q: "Is a higher-grade deposit always better?",
          a: "No. Grade must be read alongside scale, metallurgy and jurisdiction. A very high grade over a tiny resource cannot support a mine, and a high-grade deposit whose ore is refractory or carries penalty elements may be worth less than a cleaner lower-grade one. Grade tells you about cost per ounce, not about whether the project works.",
        },
        {
          q: "Why do some companies not appear in the rankings?",
          a: "Because they have no filed resource estimate. An early-stage explorer may have excellent drill results and no formal NI 43-101 resource yet, which means there is no grade or tonnage figure to rank. Absence here reflects the stage of disclosure, not the quality of the ground.",
        },
        {
          q: "Why does grade matter more than the total ounce count?",
          a: "Because grade determines how much rock must be moved and processed for each ounce recovered, and that drives the cost structure. A large low-grade resource can be entirely uneconomic while a smaller higher-grade one is profitable. Ounces tell you the size of the prize; grade tells you whether it can be won.",
        },
      ]}
    />
  );
}
