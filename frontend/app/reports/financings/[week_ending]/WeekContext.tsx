import Link from "next/link";

/**
 * Prose around the weekly financings table.
 *
 * The table on its own rendered about 200 words -- a handful of rows and three
 * headings. Nine of these were submitted to the sitemap when the archive gap
 * was fixed, which is thin content of exactly the kind the rest of this work
 * has been removing.
 *
 * Everything in the "this week" paragraph is derived from the week's own
 * numbers, so each page says something different. The explainer below it is
 * shared across weeks on purpose: it is reference material, and rewriting it
 * per page to dodge duplication would make it worse, not better.
 */

type Item = {
  company_name: string;
  ticker?: string | null;
  financing_type?: string | null;
  amount_raised_usd?: number | null;
  primary_commodity?: string | null;
  lead_agent?: string | null;
};

type Props = {
  weekLabel: string;
  count: number;
  totalUsd: number;
  items: Item[];
  byType: { type: string; count: number; amount_usd: number }[];
  byCommodity: { commodity: string; count: number; amount_usd: number }[];
};

function usd(n: number): string {
  if (!n) return "$0";
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${Math.round(n).toLocaleString()}`;
}

function label(s?: string | null): string {
  if (!s) return "";
  return s.replace(/_/g, " ");
}

/** Sentences about this week specifically, built from its own figures. */
function buildAnalysis(p: Props): string[] {
  const out: string[] = [];
  const funded = p.items.filter((i) => (i.amount_raised_usd ?? 0) > 0);
  const amounts = funded
    .map((i) => i.amount_raised_usd as number)
    .sort((a, b) => b - a);

  // Size and shape.
  let s1 = `${p.count} junior mining financing${p.count === 1 ? "" : "s"} ${p.count === 1 ? "was" : "were"} announced in the week ending ${p.weekLabel}`;
  if (p.totalUsd > 0) s1 += `, raising ${usd(p.totalUsd)} between them`;
  out.push(s1 + ".");

  if (amounts.length > 1) {
    const mean = amounts.reduce((a, b) => a + b, 0) / amounts.length;
    const largest = amounts[0];
    const share = p.totalUsd > 0 ? (largest / p.totalUsd) * 100 : 0;
    let s2 = `The average raise was ${usd(mean)}`;
    if (share >= 40) {
      s2 += `, though the week was top-heavy — the largest single deal accounted for ${Math.round(share)}% of the total`;
    } else {
      s2 += `, with the largest at ${usd(largest)} and the smallest at ${usd(amounts[amounts.length - 1])}`;
    }
    out.push(s2 + ".");
  }

  // Structure mix — what kind of paper was issued.
  if (p.byType.length) {
    const sorted = [...p.byType].sort((a, b) => b.count - a.count);
    const lead = sorted[0];
    let s3 = `${lead.count} of them ${lead.count === 1 ? "was a" : "were"} ${label(lead.type)}${lead.count === 1 ? "" : "s"}`;
    if (sorted.length > 1) {
      s3 += `, alongside ${sorted
        .slice(1)
        .map((t) => `${t.count} ${label(t.type)}${t.count === 1 ? "" : "s"}`)
        .join(" and ")}`;
    }
    out.push(s3 + ".");
  }

  // Commodity mix. "other" means the company has no commodity on file, which
  // is worth saying plainly rather than presenting as a category.
  const named = p.byCommodity.filter(
    (c) => c.commodity && c.commodity !== "other",
  );
  if (named.length) {
    const sorted = [...named].sort((a, b) => b.amount_usd - a.amount_usd);
    const top = sorted[0];
    let s4 = `By commodity, ${top.commodity} led with ${usd(top.amount_usd)} across ${top.count} deal${top.count === 1 ? "" : "s"}`;
    if (sorted.length > 1) {
      s4 += `, followed by ${sorted
        .slice(1, 3)
        .map((c) => `${c.commodity} (${usd(c.amount_usd)})`)
        .join(" and ")}`;
    }
    const unknown = p.byCommodity.find((c) => c.commodity === "other");
    if (unknown) {
      s4 += `. A further ${unknown.count} raise${unknown.count === 1 ? "" : "s"} came from companies with no primary commodity recorded`;
    }
    out.push(s4 + ".");
  }

  // Who underwrote it, where we know.
  const agents = Array.from(
    new Set(p.items.map((i) => (i.lead_agent || "").trim()).filter(Boolean)),
  );
  if (agents.length) {
    out.push(
      `Lead agents on record this week: ${agents.slice(0, 4).join(", ")}.`,
    );
  }

  return out;
}

export default function WeekContext(props: Props) {
  const analysis = buildAnalysis(props);

  return (
    <div className="mt-12 flex flex-col gap-10">
      <section>
        <h2 className="mb-3 text-xl font-bold text-slate-900">
          What the week looked like
        </h2>
        <div className="flex flex-col gap-3 leading-relaxed text-slate-700">
          {analysis.map((s, i) => (
            <p key={i}>{s}</p>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xl font-bold text-slate-900">
          How to read a financing roundup
        </h2>
        <div className="flex flex-col gap-3 leading-relaxed text-slate-700">
          <p>
            Junior explorers have no revenue, so almost every dollar they spend
            in the ground is raised by issuing shares. That makes the weekly
            financing record one of the more honest signals in the sector: it
            shows which companies can still raise, on what terms, and from whom.
          </p>
          <p>
            A <strong>private placement</strong> sells shares directly to
            selected investors, usually at a discount to market and often with a
            warrant attached. A <strong>bought deal</strong> has an underwriter
            commit to the whole raise up front, which removes financing risk
            from the company and generally signals stronger demand.{" "}
            <strong>Flow-through shares</strong> are a Canadian structure that
            passes exploration tax deductions to the buyer, so they price at a
            premium but the money must be spent on qualifying exploration.
          </p>
          <p>
            Watch the warrants rather than the headline number. A raise done
            with a half-warrant at a strike near the current price creates
            future selling pressure at a known level, and enough of them stacked
            up will cap a stock for years regardless of drill results.
          </p>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xl font-bold text-slate-900">Related</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/open-financings"
            className="rounded-lg border border-amber-700/30 px-4 py-2 text-sm text-amber-800 transition-colors hover:bg-amber-50"
          >
            Financings open now →
          </Link>
          <Link
            href="/reports/financings"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            All weekly roundups →
          </Link>
          <Link
            href="/guides/private-placements-and-warrants"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            Private placements and warrants →
          </Link>
          <Link
            href="/guides/how-junior-mining-companies-raise-money"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            How juniors raise money →
          </Link>
          <Link
            href="/investor-tools/warrant-radar"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            Warrant Overhang Radar →
          </Link>
          <Link
            href="/glossary/category/mining-finance"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            Mining finance glossary →
          </Link>
        </div>
      </section>
    </div>
  );
}
