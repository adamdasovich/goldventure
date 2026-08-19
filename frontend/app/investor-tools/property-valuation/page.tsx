import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import PropertyValuationClient from "./PropertyValuationClient";

export const revalidate = 3600;

/**
 * Checked against property_valuation in core/views/investor_tools.py: active
 * PropertyListing rows only, capped at 30, filtered by primary mineral and
 * country, with price per hectare derived from asking price / total hectares.
 */
export default function PropertyValuationPage() {
  return (
    <ToolPageLayout
      slug="property-valuation"
      badge="Marketplace"
      title="Property Valuation Tool"
      intro="Benchmark mineral property listings on a dollar-per-hectare basis by mineral and jurisdiction, so an asking price can be judged against comparable ground rather than accepted on its own terms."
      tool={<PropertyValuationClient />}
      related={["grade-ranker", "peer-comparison", "due-diligence"]}
      relatedNote={
        <>
          Browse the listings themselves on the{" "}
          <Link href="/properties" className="text-gold-400 hover:underline">
            Prospector&apos;s Property Exchange
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
                Mineral properties change hands constantly and almost none of
                the pricing is public. Unlike listed companies, where a market
                sets a value every second, a claim block is worth whatever a
                buyer and seller agree — and neither side usually has much of a
                reference point.
              </p>
              <p>
                Dollar per hectare is the crudest possible normalisation and
                also the only one generally available. It ignores everything
                that actually determines value, but it puts an asking price into
                a range, which is more than most buyers start with.
              </p>
              <p>
                This tool computes that figure across active listings and lets
                you filter by mineral and country, so a price can be read
                against the ground it is competing with.
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
                <strong className="text-slate-100">Price per hectare</strong> is
                the asking price divided by the property&apos;s area. Treat it
                as a bucket rather than a valuation: it separates properties
                priced in the tens of dollars per hectare from those in the
                thousands, which is a real distinction, and says nothing within
                a bucket.
              </p>
              <p>
                <strong className="text-slate-100">
                  Mineral and jurisdiction filters
                </strong>{" "}
                are what make the comparison meaningful at all. Gold ground in
                Nevada and lithium ground in Manitoba are not substitutes, and
                comparing across them produces a number with no content.
              </p>
              <p>
                <strong className="text-slate-100">Size</strong> matters to the
                metric itself. Large land packages almost always price lower per
                hectare than small ones, because much of a big package is
                untested ground carried along with the prospective part. A small
                high-priced block may be perfectly reasonable if the value is
                concentrated.
              </p>
              <p>
                <strong className="text-slate-100">
                  What the listing says about work done
                </strong>{" "}
                dominates everything above. Ground with historical drilling,
                geophysics or a known showing is a different asset from
                unexplored claims, at any price per hectare.
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
                Look for the property whose price sits below comparable ground
                for a reason you can dismiss, rather than the lowest price per
                hectare on the list. The cheapest ground is usually cheapest
                because nobody wants it — remote, unexplored, or in a
                jurisdiction where permitting is difficult.
              </p>
              <p>
                Prior exploration expenditure is the strongest value indicator
                available. Ground carrying historical drill data, geophysical
                surveys or documented showings has had money spent on reducing
                its uncertainty, and that work is expensive to reproduce. A
                property priced similarly to unexplored claims but carrying a
                real dataset is where genuine value tends to sit.
              </p>
              <p>
                Access and infrastructure change economics more than most buyers
                expect. A property on a road with power nearby can be explored
                for a fraction of what an equivalent fly-in package costs, and
                that difference persists through every future programme.
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
                Active listings on the exchange are filtered by primary mineral
                and country, and price per hectare is computed as asking price
                divided by total hectares wherever both are stated. The result
                set is capped, so the view is a sample of current listings
                rather than a complete market survey.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    These are asking prices, not transaction prices.
                  </strong>{" "}
                  This is the central limitation. What a seller asks and what a
                  property sells for are different numbers, and only the first
                  is visible here.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Per-hectare pricing ignores everything that matters.
                  </strong>{" "}
                  Geology, prior work, access, infrastructure and permitting
                  status all dominate value, and none of them are in the metric.
                </li>
                <li>
                  <strong className="text-slate-100">
                    The sample is small.
                  </strong>{" "}
                  Benchmarks drawn from a handful of current listings are
                  indicative at best, and a single unusual listing can shift the
                  apparent range.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Listings without a price or area are excluded
                  </strong>{" "}
                  from the per-hectare calculation, which biases the sample
                  towards sellers willing to state a number.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Jurisdiction is captured at country level,
                  </strong>{" "}
                  while permitting regimes and claim rules vary substantially by
                  province and state.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is a mineral property worth per hectare?",
          a: "The range is enormous and the metric is crude. Unexplored claims in remote areas can trade for tens of dollars per hectare, while ground with historical drilling near infrastructure reaches thousands. The figure is only useful within a single mineral and jurisdiction, and even then it is a bucket rather than a valuation.",
        },
        {
          q: "Why do larger properties usually cost less per hectare?",
          a: "Because a large package carries a great deal of untested ground alongside the prospective part. Value tends to concentrate in a small area — a showing, a structural target, a drilled zone — and the surrounding claims are staked to protect it. A small block at a high per-hectare price may be entirely reasonable if that is where the value sits.",
        },
        {
          q: "What actually determines a mineral property's value?",
          a: "Prior exploration work above all — drill data, geophysics and documented showings represent money already spent reducing uncertainty, and reproducing it is expensive. After that: access and infrastructure, which determine what every future programme costs, and permitting regime, which determines whether the work can happen at all.",
        },
        {
          q: "Are these prices what properties actually sold for?",
          a: "No. These are asking prices from current listings. Transaction prices in mineral property deals are rarely disclosed, so what is visible here is what sellers hope to achieve rather than what buyers have paid.",
        },
      ]}
    />
  );
}
