import Link from "next/link";

/**
 * Server-rendered reference section for a company profile.
 *
 * The profile page fetches company, project and news data on the server and
 * then hands all of it to a client component, so a crawler received the name,
 * a short description and nothing else: 248 words with a single <h2> on a page
 * backed by 6 projects, 5 financings and 25 press releases.
 *
 * Company profiles are the platform's largest surface -- 385 pages -- and the
 * queries that actually convert are "AUMB stock", "1911 Gold news", not the
 * site's own name. This renders the facts into HTML.
 *
 * Deliberately NOT a copy of the interactive tabs above it. The tabs are for
 * browsing; this is a factual summary: derived prose, a key-facts table,
 * aggregate financing history, and headline links. Repeating the same tables
 * twice would pad the page without helping a reader.
 */

type Project = {
  id: number;
  name: string;
  project_stage?: string | null;
  primary_commodity?: string | null;
  country?: string | null;
  province_state?: string | null;
  is_flagship?: boolean;
  resource_count?: number | null;
};

type Financing = {
  id: number;
  financing_type?: string | null;
  announced_date?: string | null;
  amount_raised_usd?: string | number | null;
  price_per_share?: string | number | null;
  has_warrants?: boolean;
};

type NewsItem = {
  id: number;
  title: string;
  release_date?: string | null;
  url?: string | null;
  release_type?: string | null;
};

type Company = {
  id: number;
  name: string;
  slug?: string | null;
  ticker_symbol?: string | null;
  exchange?: string | null;
  description?: string | null;
  headquarters_city?: string | null;
  headquarters_country?: string | null;
  market_cap_usd?: string | number | null;
  website?: string | null;
  financings?: Financing[];
};

const STAGE_LABELS: Record<string, string> = {
  early_exploration: "early exploration",
  exploration: "exploration",
  resource: "resource definition",
  pea: "PEA",
  prefeasibility: "pre-feasibility",
  feasibility: "feasibility",
  development: "development",
  production: "production",
  care_maintenance: "care and maintenance",
};

// Commodity slugs that have a landing page worth linking to.
const FACET_SLUGS: Record<string, string> = {
  gold: "gold",
  silver: "silver",
  copper: "copper",
  lithium: "lithium",
  nickel: "nickel",
  uranium: "uranium",
  cobalt: "cobalt",
  graphite: "graphite",
  ree: "rare-earths",
};

function titleCase(s?: string | null) {
  if (!s) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function fmtMoney(v?: string | number | null) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (!n || Number.isNaN(n)) return null;
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${Math.round(n).toLocaleString()}`;
}

/** Month + year, for prose where an exact day reads as clutter. */
function fmtMonthYear(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00Z` : iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    timeZone: "UTC",
  });
}

function fmtDate(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00Z` : iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

/**
 * Two or three sentences assembled from fields we hold.
 *
 * Exists because 173 of the profiles carry a description under 300 characters.
 * Against 385 near-identical templates that reads as thin and near-duplicate,
 * which is exactly what "crawled - currently not indexed" describes. Every
 * clause is conditional on real data; nothing is asserted that we do not hold.
 */
function buildSummary(
  company: Company,
  projects: Project[],
  financings: Financing[],
  news: NewsItem[],
): string[] {
  const out: string[] = [];
  const listed =
    company.ticker_symbol && company.exchange
      ? `${company.exchange.toUpperCase()}: ${company.ticker_symbol}`
      : null;

  const commodities = Array.from(
    new Set(
      projects
        .map((p) => (p.primary_commodity || "").toLowerCase())
        .filter(Boolean),
    ),
  );
  const countries = Array.from(
    new Set(projects.map((p) => (p.country || "").trim()).filter(Boolean)),
  );
  const stages = Array.from(
    new Set(
      projects.map((p) => (p.project_stage || "").trim()).filter(Boolean),
    ),
  );

  // Sentence 1 — what it is and where.
  let s1 = `${company.name}${listed ? ` (${listed})` : ""} is a mineral exploration company`;
  if (commodities.length === 1) {
    s1 = `${company.name}${listed ? ` (${listed})` : ""} is a ${commodities[0]}-focused mineral exploration company`;
  } else if (commodities.length > 1) {
    const head = commodities.slice(0, 3).join(", ");
    s1 = `${company.name}${listed ? ` (${listed})` : ""} is a mineral exploration company with projects spanning ${head}`;
  }
  if (countries.length === 1) s1 += ` with ground in ${countries[0]}`;
  else if (countries.length > 1)
    s1 += ` with ground in ${countries.slice(0, 3).join(", ")}`;
  out.push(s1 + ".");

  // Sentence 2 — portfolio shape.
  if (projects.length) {
    const flagship = projects.find((p) => p.is_flagship);
    const withResources = projects.filter((p) => (p.resource_count ?? 0) > 0);
    let s2 = `The company holds ${projects.length} project${projects.length === 1 ? "" : "s"} on file`;
    if (flagship) s2 += `, led by ${flagship.name}`;
    if (withResources.length)
      s2 += `, of which ${withResources.length} carr${withResources.length === 1 ? "ies" : "y"} a reported mineral resource`;
    else if (stages.length)
      s2 += `, at the ${STAGE_LABELS[stages[0]] || stages[0].replace(/_/g, " ")} stage`;
    out.push(s2 + ".");
  }

  // Sentence 3 — funding, only where we have it.
  const dated = financings.filter((f) => f.announced_date);
  if (dated.length) {
    const total = dated.reduce((acc, f) => {
      const n =
        typeof f.amount_raised_usd === "string"
          ? parseFloat(f.amount_raised_usd)
          : f.amount_raised_usd;
      return acc + (n && !Number.isNaN(n) ? n : 0);
    }, 0);
    const latest = dated
      .slice()
      .sort((a, b) => (a.announced_date! < b.announced_date! ? 1 : -1))[0];
    let s3 = `${dated.length} financing${dated.length === 1 ? "" : "s"} ${dated.length === 1 ? "is" : "are"} on record`;
    if (total > 0) s3 += `, totalling approximately ${fmtMoney(total)}`;
    if (latest?.announced_date)
      s3 += `, most recently in ${fmtMonthYear(latest.announced_date)}`;
    out.push(s3 + ".");
  }

  // Sentence 4 — disclosure activity. A dormant shell and an active explorer
  // look identical from a description alone; the release cadence separates them.
  const datedNews = news.filter((n) => n.release_date);
  if (datedNews.length) {
    const newest = datedNews
      .slice()
      .sort((a, b) => (a.release_date! < b.release_date! ? 1 : -1))[0];
    const financialCount = datedNews.filter(
      (n) => n.release_type === "financing",
    ).length;
    let s4 = `${datedNews.length} press release${datedNews.length === 1 ? "" : "s"} ${datedNews.length === 1 ? "is" : "are"} tracked here`;
    if (financialCount)
      s4 += `, ${financialCount} of them financing-related`;
    if (newest?.release_date)
      s4 += `, with the most recent dated ${fmtDate(newest.release_date)}`;
    out.push(s4 + ".");
  }

  return out;
}

export default function CompanyProfileContent({
  company,
  projects,
  news,
}: {
  company: Company;
  projects: Project[];
  news: NewsItem[];
}) {
  const financings = company.financings || [];
  const summary = buildSummary(company, projects, financings, news);

  const commodities = Array.from(
    new Set(
      projects
        .map((p) => (p.primary_commodity || "").toLowerCase())
        .filter(Boolean),
    ),
  );
  const jurisdictions = Array.from(
    new Set(
      projects
        .map((p) =>
          [p.province_state, p.country].filter(Boolean).join(", ").trim(),
        )
        .filter(Boolean),
    ),
  );

  const facts: [string, string][] = [];
  if (company.ticker_symbol)
    facts.push([
      "Listing",
      company.exchange
        ? `${company.exchange.toUpperCase()}: ${company.ticker_symbol}`
        : company.ticker_symbol,
    ]);
  const mc = fmtMoney(company.market_cap_usd);
  if (mc) facts.push(["Market capitalisation", mc]);
  if (projects.length)
    facts.push(["Projects on file", String(projects.length)]);
  if (commodities.length)
    facts.push(["Commodities", commodities.map(titleCase).join(", ")]);
  if (jurisdictions.length)
    facts.push(["Jurisdictions", jurisdictions.slice(0, 4).join(" · ")]);
  const hq = [company.headquarters_city, company.headquarters_country]
    .filter(Boolean)
    .join(", ");
  if (hq) facts.push(["Head office", hq]);
  if (financings.length)
    facts.push(["Financings on record", String(financings.length)]);

  const recentNews = news
    .filter((n) => n.title)
    .slice()
    .sort((a, b) => ((a.release_date || "") < (b.release_date || "") ? 1 : -1))
    .slice(0, 10);

  return (
    <div className="bg-slate-900 border-t border-slate-800">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-14 flex flex-col gap-12">
        {/* ---------- summary ---------- */}
        <section id="company-overview">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">
            About {company.name}
          </h2>
          <div className="flex flex-col gap-4 text-slate-300 leading-relaxed">
            {summary.map((s, i) => (
              <p key={i}>{s}</p>
            ))}
            {company.description && (
              <p className="text-slate-400">{company.description}</p>
            )}
          </div>
        </section>

        {/* ---------- key facts ---------- */}
        {facts.length > 0 && (
          <section id="key-facts">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">Key facts</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-slate-700 rounded-lg overflow-hidden">
                <tbody>
                  {facts.map(([k, v]) => (
                    <tr
                      key={k}
                      className="border-b border-slate-800 last:border-0"
                    >
                      <th
                        scope="row"
                        className="text-left font-medium text-slate-400 px-4 py-2.5 w-56 align-top"
                      >
                        {k}
                      </th>
                      <td className="text-slate-200 px-4 py-2.5 tabular-nums">
                        {v}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ---------- projects ---------- */}
        {projects.length > 0 && (
          <section id="projects-summary">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">Projects</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-slate-700 rounded-lg overflow-hidden">
                <thead>
                  <tr className="bg-slate-800/60 text-slate-400">
                    <th className="text-left font-medium px-4 py-2.5">
                      Project
                    </th>
                    <th className="text-left font-medium px-4 py-2.5">
                      Commodity
                    </th>
                    <th className="text-left font-medium px-4 py-2.5">
                      Location
                    </th>
                    <th className="text-left font-medium px-4 py-2.5">Stage</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id} className="border-t border-slate-800">
                      <td className="px-4 py-2.5 text-slate-200">
                        {p.name}
                        {p.is_flagship && (
                          <span className="ml-2 text-[10px] uppercase tracking-wider text-gold-400">
                            flagship
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-slate-300">
                        {titleCase(p.primary_commodity) || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-slate-300">
                        {[p.province_state, p.country]
                          .filter(Boolean)
                          .join(", ") || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-slate-300">
                        {p.project_stage
                          ? titleCase(
                              STAGE_LABELS[p.project_stage] ||
                                p.project_stage.replace(/_/g, " "),
                            )
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ---------- financing history ---------- */}
        {financings.length > 0 && (
          <section id="financing-summary">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              Financing history
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-slate-700 rounded-lg overflow-hidden">
                <thead>
                  <tr className="bg-slate-800/60 text-slate-400">
                    <th className="text-left font-medium px-4 py-2.5">
                      Announced
                    </th>
                    <th className="text-left font-medium px-4 py-2.5">Type</th>
                    <th className="text-left font-medium px-4 py-2.5">
                      Amount
                    </th>
                    <th className="text-left font-medium px-4 py-2.5">
                      Warrants
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {financings
                    .slice()
                    .sort((a, b) =>
                      (a.announced_date || "") < (b.announced_date || "")
                        ? 1
                        : -1,
                    )
                    .slice(0, 12)
                    .map((f) => (
                      <tr key={f.id} className="border-t border-slate-800">
                        <td className="px-4 py-2.5 text-slate-300 whitespace-nowrap">
                          {fmtDate(f.announced_date) || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-slate-300">
                          {f.financing_type
                            ? titleCase(f.financing_type.replace(/_/g, " "))
                            : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-slate-200 tabular-nums">
                          {fmtMoney(f.amount_raised_usd) || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-slate-300">
                          {f.has_warrants ? "Yes" : "—"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <p className="text-slate-400 text-sm mt-3">
              Warrants attached to past raises are future dilution at a fixed
              price. The{" "}
              <Link
                href="/investor-tools/warrant-radar"
                className="text-gold-400 hover:underline"
              >
                Warrant Overhang Radar
              </Link>{" "}
              tracks the resulting overhang, and the{" "}
              <Link
                href="/investor-tools/dilution-tracker"
                className="text-gold-400 hover:underline"
              >
                Dilution Tracker
              </Link>{" "}
              shows how the share count has grown.
            </p>
          </section>
        )}

        {/* ---------- recent news ---------- */}
        {recentNews.length > 0 && (
          <section id="recent-news">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              Recent news releases
            </h2>
            <ul className="flex flex-col gap-3">
              {recentNews.map((n) => (
                <li key={n.id} className="flex flex-col sm:flex-row sm:gap-4">
                  <span className="text-slate-500 text-sm whitespace-nowrap sm:w-32 shrink-0">
                    {fmtDate(n.release_date)}
                  </span>
                  {n.url ? (
                    <a
                      href={n.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-300 hover:text-gold-400 leading-snug"
                    >
                      {n.title}
                    </a>
                  ) : (
                    <span className="text-slate-300 leading-snug">
                      {n.title}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* ---------- related ---------- */}
        <section id="related">
          <h2 className="text-2xl font-bold text-gold-400 mb-4">Related</h2>
          <div className="flex flex-wrap gap-3">
            {commodities
              .filter((c) => FACET_SLUGS[c])
              .slice(0, 4)
              .map((c) => (
                <Link
                  key={c}
                  href={`/companies/commodity/${FACET_SLUGS[c]}`}
                  className="px-4 py-2 rounded-lg border border-gold-500/30 text-gold-300 hover:bg-gold-500/10 transition-colors text-sm"
                >
                  All {titleCase(c)} companies →
                </Link>
              ))}
            <Link
              href="/companies"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Company directory →
            </Link>
            <Link
              href="/open-financings"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Open financings →
            </Link>
            <Link
              href="/guides/how-to-read-ni-43-101-report"
              className="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700/40 transition-colors text-sm"
            >
              Reading an NI 43-101 →
            </Link>
          </div>
          {company.website && (
            <p className="text-slate-400 text-sm mt-5">
              Company website:{" "}
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="text-gold-400 hover:underline"
              >
                {company.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
              </a>
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
