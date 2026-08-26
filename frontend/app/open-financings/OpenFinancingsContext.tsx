import Link from "next/link";

/**
 * Server-rendered explanation beneath the open-financings table.
 *
 * The page rendered 712 words, no <h2> at all, and a single <h3> containing
 * the number 16 -- the table is a client component, so a crawler got the
 * heading and the chrome. /closed-financings was given this treatment on
 * 2026-08-23 after Google filed it under Soft 404; this page was missed.
 *
 * The content is deliberately different from the closed-financings copy. That
 * page explains what closing means and why a share price moves when dilution
 * lands. This one is about deciding whether to participate in a deal that is
 * still open, which is a different question and a different searcher.
 *
 * Appended below the interactive table rather than restructuring it: the table
 * carries login and register handlers and cannot move to the server.
 */

const BASE = "https://juniorminingintelligence.com";

const FAQS = [
  {
    q: "What is an open mining financing?",
    a: "A financing that has been announced but has not yet closed, so subscriptions are still being accepted. The company has set out the terms — price, size, and whether a warrant is attached — and is gathering commitments. Once it closes, the shares are issued and the deal disappears from this list.",
  },
  {
    q: "Who is allowed to participate in a private placement?",
    a: "In most cases, accredited investors only. Thresholds vary by jurisdiction but commonly involve income above $200,000, or net financial assets above $1 million. Canada also has the listed issuer financing exemption, introduced in 2022, which lets qualifying companies raise from the general public with a short offering document and no four-month hold, and a growing share of junior raises now use it.",
  },
  {
    q: "What should I check before subscribing?",
    a: "Four things: the price against where the stock trades, the warrant terms and their strike, the size of the raise against the company's existing share count, and what the money is actually for. A raise at a deep discount with a full warrant transfers value from existing holders to subscribers, and a raise that funds general working capital rather than a drill programme is buying time rather than progress.",
  },
  {
    q: "What is a hold period and why does it matter?",
    a: "Shares bought in a Canadian private placement typically cannot be sold for four months under National Instrument 45-102. That date is knowable in advance, and it is when subscribers who bought at a discount first become able to sell. Deals done under the listed issuer financing exemption are free-trading immediately, which changes the supply picture considerably.",
  },
  {
    q: "How do I take part in a financing listed here?",
    a: "Open the company from the table above and go to its financing page, where a Participate in Financing flow lets you register the amount you would want. Each open round shows how much interest has already been registered against the size of the raise, so you can see how it is filling. Registering interest is not a subscription agreement — it signals that you want an allocation, and the company follows up. You will still need to qualify under the relevant exemption before subscribing.",
  },
  {
    q: "Does a company raising money mean it is in trouble?",
    a: "Not by itself — an explorer with no revenue has no other way to fund drilling, so raising is the normal state rather than a warning. What is worth reading is the trend: whether successive raises are priced higher or lower, whether they are getting larger relative to the share count, and whether the company is raising into results or ahead of them.",
  },
];

export default function OpenFinancingsContext() {
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
        name: "Open Financings",
        item: `${BASE}/open-financings`,
      },
    ],
  };

  return (
    <div className="border-t border-slate-800 bg-slate-900">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-14 flex flex-col gap-12">
        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            How to read an open financing
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            <p>
              Junior explorers have no revenue. Every metre they drill is paid
              for by issuing shares, which makes the list above the clearest
              running signal in the sector: who can still raise, on what terms,
              and from whom.
            </p>
            <p>
              The headline size matters least. What decides whether a raise
              helps or hurts an existing shareholder is the discount to market,
              the warrant attached, and the size of the issue relative to the
              shares already outstanding. A small raise at a steep discount with
              a full warrant can be more dilutive in effect than a larger one
              priced at market.
            </p>
            <p>
              Warrants deserve particular attention, because they are the part
              that outlives the transaction. A half-warrant struck slightly
              above the current price creates a known ceiling: every rally into
              that strike releases new supply, and enough layers of them will
              hold a stock down regardless of what the drill returns.
            </p>
          </div>
        </section>

        {/* The page listed every open round and never told anyone they could
            act on one: zero occurrences of "participate" or "register
            interest" before 2026-08-26. The registration flow lives on each
            company's financing page and is the most actionable thing on the
            site, so it belongs in the server-rendered copy rather than only
            inside the client table. */}
        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-5">
            How this list works
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            <p>
              <strong className="text-slate-100">
                Every open round is on this page.
              </strong>{" "}
              The table above is the complete set of junior mining financings
              currently accepting subscriptions — not a selection, and not a
              weekly digest. It updates as new raises are announced, so a deal
              announced this morning appears here today rather than in a roundup
              on Friday. That timing is most of the value: a financing is only
              actionable while it is still open, and the window is often days.
            </p>
            <p>
              <strong className="text-slate-100">
                You can register interest in any of them.
              </strong>{" "}
              Open the company, and its financing page carries a{" "}
              <em>Participate in Financing</em> flow where you enter the amount
              you would want. Each round shows how much interest has already
              been registered against the size of the raise, so you can see how
              a deal is filling before you commit. Registering interest is not a
              subscription agreement — it tells the company you want an
              allocation, and the company comes back to you.
            </p>
            <p>
              <strong className="text-slate-100">
                Closed rounds stay searchable.
              </strong>{" "}
              Once a deal closes it moves to the{" "}
              <Link
                href="/closed-financings"
                className="text-gold-400 hover:underline font-medium"
              >
                closed financings database
              </Link>
              , which is the history you need to read a company properly —
              whether successive raises have been priced higher or lower, how
              much the share count has grown, and what warrant overhang those
              deals left behind.
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-5">
            Common questions
          </h2>
          <div className="flex flex-col gap-7">
            {FAQS.map((f) => (
              <div key={f.q}>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  {f.q}
                </h3>
                <p className="text-slate-300 leading-relaxed">{f.a}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-4">Related</h2>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/closed-financings"
              className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
            >
              Recently closed financings →
            </Link>
            <Link
              href="/reports/financings"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Weekly financing roundups →
            </Link>
            <Link
              href="/guides/private-placements-and-warrants"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Private placements and warrants →
            </Link>
            <Link
              href="/guides/how-junior-mining-companies-raise-money"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              How juniors raise money →
            </Link>
            <Link
              href="/investor-tools/warrant-radar"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Warrant Overhang Radar →
            </Link>
            <Link
              href="/investor-tools/dilution-tracker"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Dilution Tracker →
            </Link>
            <Link
              href="/glossary/category/mining-finance"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Mining finance glossary →
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
