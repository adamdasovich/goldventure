/**
 * Expanded context for individual glossary terms.
 *
 * The stored definitions average 40 words. A page per term built on those
 * alone would be thin, which is the whole reason the category pages came
 * first. A term only earns its own page when there is genuinely more to say
 * about it -- so a term appears here or it does not get a page, and lives on
 * its category page instead.
 *
 * Keyed by the term's anchor slug (see termAnchor in glossaryCategories.ts) so
 * a term can be renamed in the database without silently losing its expansion.
 *
 * `whyItMatters` is the investor-facing point of the term. `inPractice` is
 * where it shows up and how to read it. `pitfall` is the mistake people
 * actually make. All three are optional; anything present is rendered.
 */

export type TermExtra = {
  /** One-line framing shown under the definition. */
  summary?: string;
  whyItMatters?: string;
  inPractice?: string;
  pitfall?: string;
  /** Related glossary anchors, rendered as links. */
  seeAlso?: string[];
};

export const TERM_EXTRAS: Record<string, TermExtra> = {
  // ---------------------------------------------------------------- reporting
  "mineral-resource": {
    summary:
      "A mineral resource is rock that might one day be mined economically. It is a geological statement, not a commercial one.",
    whyItMatters:
      "Resources are the raw inventory a junior is valued on, and they are the number most often quoted in headlines. But a resource has not been shown to be profitable to extract — that only happens when it is converted to a reserve through an economic study. Companies without reserves are, in effect, asking you to underwrite that conversion.",
    inPractice:
      "Resources are reported in three confidence categories — measured, indicated and inferred — and the split matters more than the total. A deposit that is 80% inferred is a very different asset from one that is 80% measured, even at identical ounce counts.",
    pitfall:
      "Adding measured, indicated and inferred together into a single headline number is common and misleading. Inferred material cannot be used in the economic studies that turn a resource into a reserve.",
    seeAlso: [
      "measured-resource",
      "indicated-resource",
      "inferred-resource",
      "mineral-reserve",
      "cut-off-grade",
    ],
  },
  "mineral-reserve": {
    summary:
      "A mineral reserve is the part of a resource that a study has shown can be mined at a profit under stated assumptions.",
    whyItMatters:
      "Reserves are the closest thing in mining disclosure to a commercial commitment. Declaring one means a qualified person has applied real costs, real recoveries and a stated metal price and concluded the material pays for its own extraction. Very few juniors ever get there.",
    inPractice:
      "Reserves come in two categories, proven and probable, derived from measured and indicated resources respectively. The metal price assumption sits in the technical report and is worth finding — a reserve declared at $2,400 gold behaves differently at $1,700.",
    pitfall:
      "Reserves are always smaller than the resource they come from, sometimes dramatically. A company quoting only its resource may be doing so because the reserve is unflattering or does not exist.",
    seeAlso: [
      "mineral-resource",
      "proven-reserve",
      "probable-reserve",
      "feasibility-study",
    ],
  },
  "inferred-resource": {
    summary:
      "The lowest confidence resource category — estimated from limited drilling and geological inference.",
    whyItMatters:
      "Inferred material is where the option value in an explorer sits, and also where most of the disappointment comes from. It is real enough to justify more drilling and not solid enough to build a mine plan on.",
    inPractice:
      "Under NI 43-101, inferred resources cannot be included in the economic analysis of a feasibility study, and only in a limited way in a PEA. When a company upgrades inferred material to indicated, expect the tonnage to shrink and the grade to move — often downward.",
    pitfall:
      "Treating inferred ounces as equivalent to indicated or measured ounces when comparing companies on an enterprise-value-per-ounce basis. It flatters exactly the companies that deserve it least.",
    seeAlso: [
      "indicated-resource",
      "measured-resource",
      "mineral-resource",
      "drill-program",
    ],
  },
  "indicated-resource": {
    summary:
      "The middle confidence category — enough drilling to support mine planning, short of the certainty of measured.",
    whyItMatters:
      "Indicated is the threshold that matters commercially, because indicated resources can be converted to probable reserves and can carry an economic study. A company moving material from inferred to indicated is doing the work that turns a prospect into a project.",
    inPractice:
      "Drill spacing is the practical driver. Watch for infill drilling programmes described as resource conversion — that is a company spending money specifically to move a category boundary.",
    pitfall:
      "Assuming conversion is a formality. Some deposits never tighten up, because the mineralisation is genuinely erratic rather than under-drilled.",
    seeAlso: [
      "inferred-resource",
      "measured-resource",
      "probable-reserve",
      "mineral-resource",
    ],
  },
  "measured-resource": {
    summary:
      "The highest confidence resource category, supporting detailed production planning.",
    whyItMatters:
      "Measured material carries the least geological risk and is what converts to proven reserves. In practice it is concentrated in the parts of a deposit that will be mined first, which is exactly where estimation errors would hurt most.",
    inPractice:
      "Producers and near-producers carry measured resources; grassroots explorers essentially never do. Its presence tells you roughly where a company sits on the development curve without reading anything else.",
    seeAlso: ["indicated-resource", "proven-reserve", "mineral-resource"],
  },
  "proven-reserve": {
    summary:
      "The economically mineable part of a measured resource, demonstrated by a study at feasibility level.",
    whyItMatters:
      "This is the highest bar in mining disclosure. Proven reserves underpin mine financing, because lenders will not fund against material that has not cleared it.",
    pitfall:
      "Proven does not mean guaranteed. It means the geology and the economics were both demonstrated under a specific set of price and cost assumptions, all of which can move.",
    seeAlso: [
      "probable-reserve",
      "mineral-reserve",
      "measured-resource",
      "feasibility-study",
    ],
  },
  "probable-reserve": {
    summary:
      "The economically mineable part of an indicated resource — and usually the larger share of any reserve statement.",
    whyItMatters:
      "Most reserves at most mines are probable rather than proven. That is normal, not a warning sign; requiring measured confidence across an entire deposit would rarely be worth the drilling cost.",
    seeAlso: ["proven-reserve", "mineral-reserve", "indicated-resource"],
  },
  "preliminary-economic-assessment-pea": {
    summary:
      "The first economic study of a project, and the only one permitted to include inferred material.",
    whyItMatters:
      "A PEA is where a deposit first gets a dollar value attached, so it usually moves the share price more than any drill result. It is also the least rigorous study stage, and its permissiveness about inferred material is the reason.",
    inPractice:
      "Read the metal price assumption, the share of inferred material in the mine plan, and the capital cost. A PEA with 40% inferred feed and a $700M capex is a very different proposition from its headline NPV.",
    pitfall:
      "PEAs cannot be used to declare reserves, and their economics routinely deteriorate at pre-feasibility once inferred material is excluded and costs are firmed up.",
    seeAlso: [
      "feasibility-study",
      "inferred-resource",
      "net-present-value-npv",
      "internal-rate-of-return-irr",
    ],
  },
  "feasibility-study": {
    summary:
      "The most rigorous economic study stage, sufficient to support a production decision and project financing.",
    whyItMatters:
      "A feasibility study converts indicated and measured resources into reserves and is what banks lend against. Reaching it is the point at which a junior stops being an exploration story and becomes a construction financing problem.",
    inPractice:
      "Expect detailed capital and operating costs, metallurgical test work, permitting status and a defined mine plan. Compare its assumptions against the PEA that preceded it — the delta tells you how well the project held up under scrutiny.",
    seeAlso: [
      "preliminary-economic-assessment-pea",
      "mineral-reserve",
      "capital-expenditure-capex",
      "net-present-value-npv",
    ],
  },
  "cut-off-grade": {
    summary:
      "The lowest grade worth processing — the dial that decides what counts as ore and what counts as waste.",
    whyItMatters:
      "Cut-off grade is the single most powerful lever in a resource statement. Lower it and tonnage rises while average grade falls; raise it and the opposite. Two companies reporting the same deposit at different cut-offs are not comparable.",
    inPractice:
      "Cut-off is set from metal price, recovery and processing cost, so it moves with the market. Resource statements should disclose it; if a release quotes ounces without a cut-off, the number is not interpretable.",
    pitfall:
      "Comparing grades across companies without checking cut-offs. It is the most common apples-to-oranges error in junior mining.",
    seeAlso: [
      "grade-g-t",
      "mineral-resource",
      "dilution",
      "metallurgical-recovery",
    ],
  },
  "copper-equivalent-cueq": {
    summary:
      "A way of expressing a polymetallic deposit as though it were all copper, using relative metal prices.",
    whyItMatters:
      "Equivalence lets a deposit carrying copper, gold and silver be quoted as one number. It is useful for comparison and easy to flatter, because the result depends entirely on the prices and recoveries chosen.",
    pitfall:
      "Equivalent grades assume every metal is recovered and paid for. If the by-product does not report to concentrate, or is penalised by the smelter, the equivalent number overstates what is actually saleable.",
    seeAlso: [
      "silver-ounce-equivalent-ageq",
      "polymetallic-deposit",
      "metallurgical-recovery",
      "grade-g-t",
    ],
  },
  "silver-ounce-equivalent-ageq": {
    summary:
      "The silver-denominated version of metal equivalence, common in polymetallic silver deposits.",
    whyItMatters:
      "Most primary silver deposits carry meaningful lead, zinc or gold credits. AgEq lets those be expressed in one figure, but the silver-to-gold and silver-to-base-metal ratios chosen drive the result.",
    seeAlso: [
      "copper-equivalent-cueq",
      "silver-grade-g-t",
      "by-product-silver",
      "silver-gold-ratio",
    ],
  },
  "ounce-troy-ounce": {
    summary:
      "The unit precious metals are priced and reported in — 31.1035 grams, not the 28.35g of an avoirdupois ounce.",
    inPractice:
      "Grades are reported in grams per tonne while output and reserves are reported in troy ounces, so converting between the two is routine. One gram per tonne over one million tonnes is roughly 32,150 ounces.",
    seeAlso: ["grade-g-t", "silver-grade-g-t"],
  },
  "treo-total-rare-earth-oxides": {
    summary:
      "The combined oxide content of all rare earth elements in a deposit, reported as a percentage.",
    whyItMatters:
      "TREO is the headline grade for rare earth projects, and on its own it says very little. Almost all the value sits in four magnet metals — neodymium, praseodymium, dysprosium and terbium — so the split within TREO matters far more than the total.",
    pitfall:
      "A high TREO grade dominated by cerium and lanthanum, which are abundant and cheap, can be worth less than a lower TREO grade rich in magnet metals.",
    seeAlso: [
      "magnetic-rare-earths",
      "heavy-rare-earths-hree",
      "light-rare-earths-lree",
      "ree-rare-earth-elements",
      "ndpr-oxide",
    ],
  },
  "silver-grade-g-t": {
    summary: "Silver content per tonne of rock, in grams.",
    inPractice:
      "Silver grades run one to two orders of magnitude higher than gold grades for comparable economics — 100 g/t Ag is an ordinary number where 100 g/t Au would be extraordinary. Judge silver grades against silver deposits only.",
    seeAlso: [
      "grade-g-t",
      "silver-ounce-equivalent-ageq",
      "epithermal-silver-deposit",
    ],
  },
  // ------------------------------------------------------------------ finance
  "private-placement": {
    summary:
      "The main way a junior raises money: shares sold directly to selected investors, usually at a discount and often with a warrant attached.",
    whyItMatters:
      "Explorers have no revenue, so placements are the entire funding mechanism. Who participates tells you a great deal — an insider-heavy raise reads differently from one led by an institution, and a raise that closes below its announced size reads differently again.",
    inPractice:
      "Watch the discount to market, the warrant terms, and whether the deal was upsized or cut. Canadian placements carry a four-month hold period, after which that stock becomes free-trading — a date worth marking.",
    pitfall:
      "Assuming a completed raise is unambiguously good news. It is dilution, and if it is done at a deep discount with a full warrant, existing holders are paying for it.",
    seeAlso: [
      "warrant",
      "flow-through-shares",
      "accredited-investor",
      "dilution",
    ],
  },
  warrant: {
    summary:
      "A right to buy shares at a fixed price before a fixed date, usually handed out as a sweetener alongside a placement.",
    whyItMatters:
      "Warrants are future dilution at a price you already know. Enough of them clustered near the current share price will cap a stock for years, because every rally into that strike releases new supply.",
    inPractice:
      "Find the strike prices and expiry dates in the financing releases, then compare them to where the stock trades. Warrants deep in the money are effectively shares already; warrants far out of the money and near expiry are usually irrelevant.",
    pitfall:
      "Reading share count alone. A company with modest shares outstanding and a large warrant overhang is more diluted than it looks.",
    seeAlso: ["private-placement", "dilution", "flow-through-shares"],
  },
  "flow-through-shares": {
    summary:
      "A Canadian structure that passes exploration tax deductions to the buyer, so the shares price at a premium but the money is ring-fenced for exploration.",
    whyItMatters:
      "Flow-through money can only be spent on qualifying Canadian exploration. That is good for shareholders — it funds drilling rather than salaries — but it also means a company flush with flow-through cash may still be short of money for anything else.",
    inPractice:
      "Flow-through raises often price above market because the tax benefit is worth something to the buyer. A premium raise is not evidence of strong demand for the equity itself.",
    pitfall:
      "Flow-through buyers are frequently tax-motivated rather than mining-motivated, and a portion sells as soon as the hold period ends. Year-end flow-through rounds often carry a predictable overhang into the new year.",
    seeAlso: [
      "private-placement",
      "accredited-investor",
      "greenfield-exploration",
    ],
  },
  "all-in-sustaining-cost-aisc": {
    summary:
      "What it actually costs a producer to keep producing an ounce — mining, processing, overheads and sustaining capital.",
    whyItMatters:
      "AISC is the number that decides whether a mine makes money. The gap between AISC and the metal price is the margin, and it is a far better comparison across producers than cash cost, which excludes too much.",
    inPractice:
      "Compare AISC to the prevailing metal price rather than across commodities. A producer at $1,400 AISC with gold at $2,400 has room; the same producer has none at $1,500 gold.",
    pitfall:
      "AISC is a guidance metric, not a standardised accounting one. Companies vary in what they include, particularly growth capital, so read the footnotes before comparing two miners.",
    seeAlso: [
      "operating-expenditure-opex",
      "capital-expenditure-capex",
      "mining-recovery",
    ],
  },
  "net-present-value-npv": {
    summary:
      "The value of a project's future cash flows discounted back to today — the headline number of every economic study.",
    whyItMatters:
      "NPV is how a deposit becomes a dollar figure, and it is the number most often compared to a company's market cap. A project trading at a fraction of its NPV may be cheap, or the market may simply disbelieve the assumptions.",
    inPractice:
      "Always read NPV with its discount rate and metal price. Junior studies typically use 5% or 8%; a lower rate and a bullish price will roughly double the same project's stated value.",
    pitfall:
      "Treating NPV as a valuation. It ignores financing, dilution and the years of execution risk between a study and a producing mine.",
    seeAlso: [
      "internal-rate-of-return-irr",
      "payback-period",
      "preliminary-economic-assessment-pea",
      "feasibility-study",
    ],
  },
  "internal-rate-of-return-irr": {
    summary:
      "The discount rate at which a project's NPV would be zero — its implied annual return.",
    whyItMatters:
      "IRR is how a project is judged against the cost of building it. Financiers generally want to see well above 20% on a junior project, because the study assumptions rarely survive contact with construction.",
    pitfall:
      "IRR is highly sensitive to the timing of early cash flows, which flatters projects with small starter pits and back-loaded capital. Read it alongside NPV and capex, never alone.",
    seeAlso: [
      "net-present-value-npv",
      "payback-period",
      "capital-expenditure-capex",
    ],
  },
  "capital-expenditure-capex": {
    summary:
      "The upfront cost of building the mine, before it produces anything.",
    whyItMatters:
      "Capex is the number that decides whether a junior can realistically develop its own project. A company with a $60M market cap and a $900M capex is not going to build it — it is an acquisition candidate, and should be valued as one.",
    inPractice:
      "Compare capex against market capitalisation to see how much dilution or debt financing the project implies. Also watch for capex inflation between study stages, which has been severe across the sector.",
    seeAlso: [
      "operating-expenditure-opex",
      "feasibility-study",
      "net-present-value-npv",
      "payback-period",
    ],
  },
  "operating-expenditure-opex": {
    summary:
      "The recurring cost of running the mine once it is built, usually quoted per tonne or per ounce.",
    whyItMatters:
      "Opex determines whether a mine survives a downturn. High-capex, low-opex projects endure weak prices; the reverse gets shut in.",
    seeAlso: [
      "capital-expenditure-capex",
      "all-in-sustaining-cost-aisc",
      "stripping-ratio",
    ],
  },
  "payback-period": {
    summary: "How long the mine takes to earn back its construction cost.",
    whyItMatters:
      "In a cyclical industry, a short payback is worth a great deal, because it reduces how much of the return depends on where prices sit a decade out. Under three years is strong for a junior project.",
    seeAlso: [
      "net-present-value-npv",
      "internal-rate-of-return-irr",
      "capital-expenditure-capex",
    ],
  },
  "junior-mining-company": {
    summary:
      "An exploration or development-stage miner, typically with no revenue and a market capitalisation well under $500M.",
    whyItMatters:
      "Juniors are the discovery end of the industry. They carry the highest failure rate and the highest leverage to a find, and because they have no revenue their share count only ever goes one way.",
    inPractice:
      "Most trade on the TSX Venture Exchange or comparable junior boards. Assess them on cash position, burn rate, share structure and quality of ground — earnings multiples are meaningless here.",
    seeAlso: [
      "tsxv-tsx-venture-exchange",
      "private-placement",
      "dilution",
      "greenfield-exploration",
    ],
  },
  "accredited-investor": {
    summary:
      "An investor meeting income or net-worth thresholds, and therefore permitted to buy into private placements.",
    whyItMatters:
      "Placements are where juniors are funded, and they are largely closed to retail investors. Accreditation is the line that decides who gets to buy at the discount and who buys later in the open market.",
    inPractice:
      "Thresholds vary by jurisdiction but commonly involve income above $200,000 or net financial assets above $1 million. Other exemptions exist, including the Canadian listed-issuer financing exemption used by many recent raises.",
    seeAlso: ["private-placement", "retail-investor", "flow-through-shares"],
  },
  "retail-investor": {
    summary:
      "An individual investing their own money, generally buying in the open market rather than in placements.",
    whyItMatters:
      "Retail buyers usually supply the exit liquidity for placement participants whose four-month hold has expired. Knowing when those holds come off matters more than it sounds.",
    seeAlso: ["accredited-investor", "private-placement", "warrant"],
  },
  "tsxv-tsx-venture-exchange": {
    summary:
      "The Canadian junior board where most of the world's exploration companies are listed.",
    whyItMatters:
      "The TSXV concentrates junior mining capital and sets much of the disclosure culture, since NI 43-101 applies to its issuers. A TSXV listing is why so much global exploration reporting follows Canadian standards.",
    inPractice:
      "Tickers carry a .V suffix on many data services. Companies that grow out of the venture board graduate to the main TSX, which is usually a positive signal about size and liquidity.",
    seeAlso: ["junior-mining-company", "ni-43-101", "qualified-person"],
  },
  "silver-streaming-agreement": {
    summary:
      "An upfront payment in exchange for the right to buy future silver production at a fixed low price.",
    whyItMatters:
      "Streams fund construction without issuing shares, which is why developers reach for them. The cost is permanent: a share of the mine's best metal is sold cheaply for the life of the asset.",
    pitfall:
      "A stream looks like non-dilutive financing and behaves like a very long-dated liability. Check what share of by-product silver is committed before valuing that credit.",
    seeAlso: [
      "by-product-silver",
      "primary-silver-producer",
      "capital-expenditure-capex",
    ],
  },
  "silver-gold-ratio": {
    summary:
      "How many ounces of silver one ounce of gold buys — a long-watched relative-value gauge.",
    inPractice:
      "The ratio has historically moved in a wide band, widening when investors are defensive and compressing in strong precious-metal markets. Silver equities tend to move more violently than the ratio itself.",
    seeAlso: [
      "silver-ounce-equivalent-ageq",
      "precious-metals-basket",
      "silver-grade-g-t",
    ],
  },
};

/** Whether a term has enough expansion to justify its own page. */
export function hasTermPage(anchor: string): boolean {
  const extra = TERM_EXTRAS[anchor];
  if (!extra) return false;
  const bodies = [
    extra.summary,
    extra.whyItMatters,
    extra.inPractice,
    extra.pitfall,
  ].filter(Boolean) as string[];
  // Two substantial sections is the floor; anything less is a category-page
  // entry, not a page.
  return bodies.length >= 2;
}

/** Anchors that should get their own page, in a stable order. */
export function termPageAnchors(): string[] {
  return Object.keys(TERM_EXTRAS).filter(hasTermPage).sort();
}
