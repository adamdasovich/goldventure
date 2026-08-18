import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import ResourceGrowthClient from "./ResourceGrowthClient";

export const revalidate = 3600;

/**
 * Content checked against resource_growth in core/views/investor_tools.py:
 * ResourceEstimate rows per project ordered by report_date and grouped by
 * report, with the category breakdown from ResourceEstimate.RESOURCE_CATEGORIES.
 * Only companies with resource estimates on record appear in the picker.
 */
export default function ResourceGrowthPage() {
  return (
    <ToolPageLayout
      slug="resource-growth"
      badge="Resource Analysis"
      title="Resource Growth Tracker"
      intro="Watch how a company's mineral resource has changed across successive NI 43-101 reports — contained ounces, grade and tonnage — so genuine discovery can be told apart from reclassification and cut-off changes."
      tool={<ResourceGrowthClient />}
      related={["peer-comparison", "dilution-tracker", "grade-ranker"]}
      relatedNote={
        <>
          Resource growth is only good news if it outpaced the share count —
          check the{" "}
          <Link
            href="/investor-tools/dilution-tracker"
            className="text-gold-400 hover:underline"
          >
            Dilution Tracker
          </Link>
          . For what the categories mean, see{" "}
          <Link
            href="/guides/inferred-vs-indicated-vs-measured-resources"
            className="text-gold-400 hover:underline"
          >
            inferred vs indicated vs measured
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
                A resource estimate is a snapshot, and companies quote the
                latest one. What they rarely present is the sequence — how this
                estimate compares with the one before it, and the one before
                that.
              </p>
              <p>
                The sequence is where the information is. &ldquo;Two million
                ounces&rdquo; means something quite different depending on
                whether the last estimate said one million or three. And a
                headline increase can be produced without any new discovery at
                all: reclassify inferred material into indicated, lower the
                cut-off grade so marginal rock qualifies, or fold in an acquired
                deposit, and the ounce count rises without a drill turning.
              </p>
              <p>
                This tool lines up every resource estimate a company has filed
                and shows contained ounces, average grade and tonnage across
                them — so the question &ldquo;did the deposit actually
                grow?&rdquo; can be answered rather than assumed.
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
                <strong className="text-slate-100">Contained ounces</strong> is
                the headline figure and the one companies lead with. Read it
                alongside the other two columns rather than alone.
              </p>
              <p>
                <strong className="text-slate-100">Average grade</strong> is the
                critical companion. If ounces rose and grade fell materially,
                the additional ounces are lower quality than the original ones —
                often the signature of a reduced cut-off grade rather than a
                better deposit.
              </p>
              <p>
                <strong className="text-slate-100">Tonnage</strong> completes
                the picture. Ounces are grade multiplied by tonnage, so a rise
                in ounces driven entirely by tonnage at falling grade is a
                different event from one driven by both rising together.
              </p>
              <p>
                <strong className="text-slate-100">Category breakdown</strong>{" "}
                shows how much sits in each confidence class. Movement from
                inferred into indicated and measured is real progress even
                without a single extra ounce, because it means the geology is
                better understood and the material can be used in economic
                studies. Growth that stays entirely in the inferred column is
                the least valuable kind.
              </p>
              <p>
                <strong className="text-slate-100">Report dates</strong> matter
                because they set the pace. A resource that has not been updated
                in several years suggests drilling stopped, which is usually a
                funding story rather than a geological one.
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
                The best pattern is ounces rising while grade holds steady or
                improves. That means the company is finding more of the same
                quality material, or better — genuine discovery rather than
                accounting.
              </p>
              <p>
                Equally valuable, and much less celebrated, is material
                migrating up the confidence categories. A resource moving from
                mostly inferred to mostly indicated has become usable in a
                feasibility study, which is the gateway to financing and
                permitting. Nothing about the deposit changed; what changed is
                how well it is known, and that is what turns ounces into a
                project.
              </p>
              <p>
                Treat rising ounces at falling grade with suspicion. It is often
                legitimate — a lower metal price environment genuinely changes
                what is economic — but it is also the easiest way to manufacture
                a growth headline. Check whether the cut-off grade changed
                between reports.
              </p>
              <p>
                Finally, set resource growth against share count growth. A
                company that doubled its resource while tripling its shares has
                gone backwards on a per-share basis, which is the number that
                actually determines your return.
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
                Resource estimates are taken from filed NI 43-101 technical
                reports, grouped by project and ordered by report date. A single
                report typically lists several categories, which are combined
                for the totals and also shown separately so the confidence mix
                is visible. Only companies with resource estimates on record can
                be charted.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Cut-off grade changes are not automatically flagged.
                  </strong>{" "}
                  A change in cut-off between reports can move ounces
                  substantially with no new drilling. The cut-off is stated in
                  the report itself, and comparing two estimates on different
                  cut-offs is not a like-for-like comparison.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Metal price assumptions differ between reports.
                  </strong>{" "}
                  An estimate prepared at a higher assumed price will classify
                  more material as economic, so part of any increase may simply
                  reflect a more optimistic input.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Acquisitions appear as growth.
                  </strong>{" "}
                  Ounces added by buying a deposit look identical to ounces
                  added by drilling one, and cost shareholders very differently.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Resources are not reserves.
                  </strong>{" "}
                  A resource says material exists; a reserve says it can be
                  mined economically under a specific plan. Growth in resources
                  does not imply growth in anything anyone will ever extract.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Coverage depends on reports being filed and processed.
                  </strong>{" "}
                  Companies that have never published a resource estimate cannot
                  appear, and a very recent report may not yet be reflected.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "How can a mining company's resource grow without new drilling?",
          a: "Several ways. Reclassifying inferred material into indicated or measured raises the confidence categories without adding ounces. Lowering the cut-off grade brings previously uneconomic rock into the estimate. Raising the assumed metal price has the same effect. Acquiring another deposit adds ounces outright. All produce a larger headline number, and none require a drill to turn.",
        },
        {
          q: "Why does average grade matter when ounces are rising?",
          a: "Because ounces are grade multiplied by tonnage, so the same ounce increase can mean very different things. Ounces up with grade steady means more of the same quality material. Ounces up with grade materially down usually means lower-quality rock has been brought into the estimate, most often through a reduced cut-off grade.",
        },
        {
          q: "Is moving ounces from inferred to indicated actually progress?",
          a: "Yes, and it is undervalued. Inferred material cannot be used in a feasibility study, so it cannot support financing or a mine plan. Converting it to indicated or measured makes it usable — the deposit has not changed but its economic status has, which is the step that turns ounces into a project.",
        },
        {
          q: "What is the difference between a resource and a reserve?",
          a: "A resource is a statement that mineralised material exists in a defined quantity and grade. A reserve is the portion of it demonstrated to be economically mineable under a specific plan, with the necessary studies and permits behind it. Resource growth does not imply that anything will ever be extracted.",
        },
        {
          q: "How often should a company update its resource estimate?",
          a: "There is no fixed schedule; updates follow meaningful drilling. A gap of several years usually indicates that drilling stopped, which more often reflects the state of the treasury than the state of the geology. A steady cadence of updates suggests a funded, active programme.",
        },
      ]}
    />
  );
}
