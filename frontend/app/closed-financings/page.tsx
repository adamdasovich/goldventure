import Link from "next/link";
import ClosedFinancingsClient from "./ClosedFinancingsClient";

const BASE = "https://juniorminingintelligence.com";

// Metadata + canonical live in layout.tsx.
export const revalidate = 3600;

/**
 * Server shell for /closed-financings.
 *
 * The page is 1,100 lines but rendered only 88 words to a crawler: it is a
 * client component whose financing table loads after hydration, so the HTML
 * carried a heading and nothing else. Google reported it under Soft 404 on
 * 2026-08-23, which is the correct reading of a page with no content.
 *
 * The interactive table keeps its own SiteHeader because that takes login and
 * register handlers and cannot move to the server. So rather than splitting the
 * component apart, the explanatory content is appended below it — same effect
 * for indexing, far less disturbance to a working page.
 */

const FAQS = [
  {
    q: "What does it mean when a mining financing closes?",
    a: "Closing is the point at which the money actually changes hands: subscribers pay, the company issues the shares, and the funds land in treasury. Announcing a financing and closing one are different events, sometimes weeks apart, and a deal announced is not a deal completed. Larger raises frequently close in tranches, so the same financing can appear more than once as successive portions settle.",
  },
  {
    q: "Why does a company's share price often fall when a financing closes?",
    a: "Because closing is the moment dilution becomes real. New shares enter the market, and subscribers who bought at a discount to the market price can sell once any hold period expires. In Canada a private placement typically carries a four-month hold under National Instrument 45-102, so the selling pressure often arrives on a predictable schedule rather than immediately.",
  },
  {
    q: "What is a tranche?",
    a: "A portion of a larger financing that closes separately. A company raising ten million dollars may close six million in a first tranche and the balance weeks later, usually because subscriptions arrived at different times or regulatory approvals landed unevenly. A first tranche materially smaller than the announced total can indicate the raise is finding less demand than hoped.",
  },
  {
    q: "Does a closed financing tell me the company is well funded?",
    a: "Only in combination with what it was spending. A raise is meaningful relative to the burn rate and the programme it funds. The more useful question is how much was raised, at what price relative to the market, how much dilution it created, and whether the previous raise was at a higher or lower price.",
  },
];

export default function ClosedFinancingsPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE },
      {
        "@type": "ListItem",
        position: 2,
        name: "Closed Financings",
        item: `${BASE}/closed-financings`,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />

      <ClosedFinancingsClient />

      {/* ---------- server-rendered explanatory content ---------- */}
      <div className="bg-slate-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-14 flex flex-col gap-14 border-t border-slate-800">
          <section id="what-this-is">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              What a closed financing tells you
            </h2>
            <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
              <p>
                Junior mining companies have no revenue. Every drill hole,
                geologist and permit application is paid for by issuing new
                shares, which makes the financing record the closest thing the
                sector has to an operating statement. A company that has just
                closed a raise can fund a programme; one that has not raised in
                two years usually cannot.
              </p>
              <p>
                Closing is the moment that matters. Announcing a financing and
                completing one are separate events, often weeks apart, and deals
                are downsized or abandoned between the two. The record below
                covers rounds that actually settled — the money reached
                treasury, and the shares exist.
              </p>
              <p>
                Read each entry against the company&apos;s share price at the
                time. A raise priced close to market is a sign of genuine
                demand; a steep discount means the company had to pay for the
                capital, and the discount is a fair measure of how badly it
                needed the money.
              </p>
            </div>
          </section>

          <section id="how-to-read">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              How to read the record
            </h2>
            <div className="flex flex-col gap-5">
              <div>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  Amount raised and price
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  Judge the amount against the size of the company rather than
                  in isolation. A five-million-dollar raise is transformative
                  for a fifteen-million-dollar company and routine for a
                  three-hundred-million-dollar one. The price tells you what the
                  market would pay on the day.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  Financing type
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  Private placements are the sector&apos;s default. Bought deals
                  signal that an underwriter was willing to take inventory risk,
                  which is a stronger endorsement. Flow-through shares carry a
                  Canadian tax benefit and therefore price at a premium, so the
                  headline price is not comparable to an ordinary placement.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  Tranches
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  Large raises frequently close in stages, so one financing can
                  appear more than once. A first tranche much smaller than the
                  announced total is worth noticing: it often means demand fell
                  short of the plan.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  Warrants attached
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  Most placements bundle a fraction of a warrant with each
                  share. That warrant is future dilution at a fixed price, and
                  it caps the share price near the strike once the stock
                  recovers. The{" "}
                  <Link
                    href="/investor-tools/warrant-radar"
                    className="text-gold-400 hover:underline"
                  >
                    Warrant Overhang Radar
                  </Link>{" "}
                  tracks the resulting overhang across the market.
                </p>
              </div>
            </div>
          </section>

          <section id="context">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              Putting a raise in context
            </h2>
            <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
              <p>
                A single financing means little on its own. The sequence is what
                matters: a company raising at progressively higher prices is
                being rewarded by the market and issuing fewer shares for each
                dollar it needs. One raising at successively lower prices is
                caught in the cycle that destroys junior mining returns, because
                a weaker price means more shares next time, which weakens the
                price further.
              </p>
              <p>
                The{" "}
                <Link
                  href="/investor-tools/dilution-tracker"
                  className="text-gold-400 hover:underline"
                >
                  Dilution Tracker
                </Link>{" "}
                shows that sequence per company, and the{" "}
                <Link
                  href="/investor-tools/financing-flow"
                  className="text-gold-400 hover:underline"
                >
                  Financing Flow Tracker
                </Link>{" "}
                shows where capital is moving across the sector as a whole —
                which commodity is attracting money, and whether the window is
                opening or closing.
              </p>
              <p>
                For rounds still open to subscription, see{" "}
                <Link
                  href="/open-financings"
                  className="text-gold-400 hover:underline"
                >
                  open financings
                </Link>
                . For the mechanics of each instrument, our guide to{" "}
                <Link
                  href="/guides/how-junior-mining-companies-raise-money"
                  className="text-gold-400 hover:underline"
                >
                  how junior mining companies raise money
                </Link>{" "}
                covers placements, bought deals, flow-through shares and
                warrants with the dilution arithmetic worked through.
              </p>
            </div>
          </section>

          <section id="faq">
            <h2 className="text-2xl font-bold text-gold-400 mb-5">
              Frequently asked questions
            </h2>
            <div className="flex flex-col gap-5">
              {FAQS.map((f) => (
                <div key={f.q} className="glass-card rounded-xl p-5">
                  <h3 className="text-base font-semibold text-slate-100 mb-2">
                    {f.q}
                  </h3>
                  <p className="text-slate-300 leading-relaxed">{f.a}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
