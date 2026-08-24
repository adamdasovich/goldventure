import Link from "next/link";

/**
 * Server-rendered copy appended below each store category listing.
 *
 * The store pages are client components whose product grids load after
 * hydration, so they rendered 88-97 words to a crawler and Google reported
 * them under Soft 404 on 2026-08-23. This adds indexable content without
 * touching the working commerce UI.
 *
 * Deliberately shorter than the editorial pages. A shop page exists to sell,
 * and burying the products under an essay would trade a soft-404 flag for a
 * worse conversion rate. Roughly 250 words each is enough to be a real page.
 */

type Category = "store" | "vault" | "field-gear" | "resource-library";

const COPY: Record<
  Category,
  { heading: string; paras: string[]; faqs: { q: string; a: string }[] }
> = {
  store: {
    heading: "About the GoldVenture Store",
    paras: [
      "The store carries three kinds of thing: mineral specimens and collectible bullion, field equipment for people who actually go into the bush, and reference material for anyone learning to read a drill result or a technical report.",
      "It exists because the audience for a junior mining research platform overlaps almost entirely with the audience for a decent hand lens. Prospectors, geologists, collectors and investors tend to be the same people at different times of the week.",
      "Specimens are documented individually rather than sold as generic lots, and gear is chosen on the basis that it has to survive a field season rather than look good in a photograph.",
    ],
    faqs: [
      {
        q: "What does the GoldVenture Store sell?",
        a: "Three categories: The Vault holds mineral specimens and collectible bullion, Field Gear covers equipment and apparel for prospecting and geological work, and the Resource Library carries reference material on mining, geology and resource investing.",
      },
    ],
  },
  vault: {
    heading: "About The Vault",
    paras: [
      "The Vault holds mineral specimens, collectible bullion and geological artifacts. Each piece is listed individually with its own documentation rather than sold from an undifferentiated stock, because provenance is most of what separates a specimen from a rock.",
      "Specimen collecting sits close to the analytical side of mining. Learning to recognise mineralisation in the hand — sulphide textures, alteration halos, vein structures — is the same skill that lets you read a core photograph in a technical report with any confidence.",
      "If you are new to this, our glossary covers the terminology that appears in specimen descriptions, and the gold grade guide explains why visible gold in a hand sample says far less about a deposit than most people assume.",
    ],
    faqs: [
      {
        q: "Are the specimens authenticated?",
        a: "Each piece is listed with its own documentation covering, where known, the locality it came from and its mineralogy. Provenance is what distinguishes a documented specimen from an unattributed one, so it is recorded per item rather than claimed generally.",
      },
      {
        q: "Does visible gold in a specimen indicate a rich deposit?",
        a: "Not reliably. Visible gold is striking in a hand sample and can occur in deposits whose average grade is unremarkable, because gold distribution is often extremely erratic. Grade is an average across tonnes of rock, which is why assay results matter more than any single specimen.",
      },
    ],
  },
  "field-gear": {
    heading: "About Field Gear",
    paras: [
      "Field gear covers the equipment prospecting and geological work actually requires: hand lenses, hammers and chisels, sample bags, streak plates, magnets and acid bottles, along with apparel that holds up to a season outdoors.",
      "The selection is weighted towards things that get used rather than displayed. A 10x loupe, a decent rock hammer and a way to label samples in the rain will do more work than most of what gets marketed to the hobby.",
      "Anyone moving from collecting into genuine prospecting should pair the gear with the reading. Understanding what a drill intercept means, and how a resource estimate is built from sampling, changes what you look for in the field.",
    ],
    faqs: [
      {
        q: "What equipment does a beginner prospector actually need?",
        a: "Very little to start: a 10x hand lens, a geological hammer, sample bags with a reliable way to label them, and a means of recording where each sample came from. A streak plate, a magnet and a small acid bottle cover most basic mineral identification. Everything beyond that follows from the specific ground you are working.",
      },
      {
        q: "What magnification should a hand lens be?",
        a: "10x is the standard for field work. It resolves grain texture and mineral habit while keeping enough depth of field and working distance to be usable outdoors in poor light. Higher magnifications narrow the field of view and become difficult to hold steady.",
      },
    ],
  },
  "resource-library": {
    heading: "About the Resource Library",
    paras: [
      "The Resource Library carries reference material on geology, mining and resource investing — the background reading that makes a technical report legible rather than intimidating.",
      "Most of the analytical work on this platform assumes a working vocabulary: cut-off grade, strip ratio, resource category, net present value. Those ideas are not difficult, but they are rarely explained in one place, and the gap keeps otherwise capable investors reliant on other people's summaries.",
      "Our own guides cover the ground free of charge, and the library is for going deeper than an article reasonably can.",
    ],
    faqs: [
      {
        q: "What should I read first to understand junior mining?",
        a: "Start with how a resource estimate is built and what the categories mean, then how to read a technical report, then how these companies are financed. Those three together explain most of what moves a junior mining share price.",
      },
    ],
  },
};

export default function StoreCategoryContent({
  category,
}: {
  category: Category;
}) {
  const c = COPY[category];

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: c.faqs.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };

  return (
    <div className="bg-slate-900">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-14 flex flex-col gap-10 border-t border-slate-800">
        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-4">{c.heading}</h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            {c.paras.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-5">
            Frequently asked questions
          </h2>
          <div className="flex flex-col gap-5">
            {c.faqs.map((f) => (
              <div key={f.q} className="glass-card rounded-xl p-5">
                <h3 className="text-base font-semibold text-slate-100 mb-2">
                  {f.q}
                </h3>
                <p className="text-slate-300 leading-relaxed">{f.a}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            Learn the background
          </h2>
          <div className="flex flex-wrap gap-3">
            {[
              { href: "/glossary", label: "Mining glossary" },
              {
                href: "/guides/gold-grade-explained",
                label: "Gold grade explained",
              },
              {
                href: "/guides/how-to-interpret-mining-drill-results",
                label: "Reading drill results",
              },
              {
                href: "/guides/how-to-read-ni-43-101-report",
                label: "Reading an NI 43-101 report",
              },
              { href: "/guides", label: "All guides" },
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
              >
                {l.label} →
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
