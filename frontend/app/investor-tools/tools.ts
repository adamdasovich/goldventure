/**
 * Tool catalogue for /investor-tools.
 *
 * Deliberately framework-free (no "use client") so both the server-rendered
 * index page and the interactive grid can import it. The page needs the data to
 * render headings and prose into the HTML; the grid needs it to render cards
 * behind the auth check. One list, so the two cannot drift.
 */

export type ToolGroupId =
  "screen" | "value" | "capital" | "quality" | "diligence";

export type Tool = {
  title: string;
  slug: string;
  description: string;
  href: string;
  badge: string;
  icon: string;
  available: boolean;
  group: ToolGroupId | null;
};

/** Tools any signed-out visitor can open. */
export const FREE_TOOL_SLUGS = ["grade-ranker", "sector-pulse"];

// Mirrors MINER_TOOLS in backend/core/entitlements.py, which is the authority.
// Empty since the Miner tier was retired on 2026-08-31: warrant-radar moved to
// Prospector, which now gets every tool. Kept so the two stay in step if a
// tool is ever put behind a higher tier again.
export const MINER_TOOL_SLUGS: string[] = [];

export const TOOLS: Tool[] = [
  {
    title: "Stock Performance Comparator",
    slug: "stock-comparator",
    description:
      "Compare the share-price performance of up to 10 companies side by side. Normalized return curves, rankings, and volatility over any window.",
    href: "/investor-tools/stock-comparator",
    badge: "Analysis",
    icon: "M3 3v18h18M18.5 9.5l-5 5-3-3-4 4",
    available: true,
    group: "value",
  },
  {
    title: "Metal Leverage Analyzer",
    slug: "metal-correlation",
    description:
      "Measure how tightly each stock tracks a chosen metal and how much it amplifies moves. Correlation, beta, R², and a volatility leverage ratio across up to 10 companies.",
    href: "/investor-tools/metal-correlation",
    badge: "Commodity Leverage",
    icon: "M3 12h3l3-9 4 18 3-9h5",
    available: true,
    group: "value",
  },
  {
    title: "Resource Growth Tracker",
    slug: "resource-growth",
    description:
      "See how a company's mineral resource estimates have grown across successive NI 43-101 reports — contained ounces, grade, and tonnage over time.",
    href: "/investor-tools/resource-growth",
    badge: "Resource Analysis",
    icon: "M3 17l6-6 4 4 8-8M17 7h4v4",
    available: true,
    group: "value",
  },
  {
    title: "Liquidity & Days to Exit",
    slug: "liquidity-screener",
    description:
      "How long it would actually take to sell a position. Median daily volume, sellable-per-day, and days-to-exit for any position size — the risk no other screener shows.",
    href: "/investor-tools/liquidity-screener",
    badge: "Market Quality",
    icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z",
    available: true,
    group: "quality",
  },
  {
    title: "Signal-to-Noise Ratio",
    slug: "signal-to-noise",
    description:
      "What share of a company's news reports an actual result — drill intercepts, resource updates, studies — versus corporate filler. Tells explorers from promoters.",
    href: "/investor-tools/signal-to-noise",
    badge: "Market Quality",
    icon: "M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3",
    available: true,
    group: "quality",
  },
  {
    title: "Warrant Overhang Radar",
    slug: "warrant-radar",
    description:
      "Every live warrant tranche in the market: what a stock must reach before they're exercisable, the cash that lands in treasury when they are, and when the overhang expires.",
    href: "/investor-tools/warrant-radar",
    badge: "Capital Structure",
    icon: "M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33",
    available: true,
    group: "capital",
  },
  {
    title: "Dilution Tracker",
    slug: "dilution-tracker",
    description:
      "Track a company's share dilution from its financing history — shares issued per raise, cumulative dilution, and outstanding warrant overhang.",
    href: "/investor-tools/dilution-tracker",
    badge: "Capital Structure",
    icon: "M12 3l8 4-8 4-8-4 8-4zM4 11l8 4 8-4M4 15l8 4 8-4",
    available: true,
    group: "capital",
  },
  {
    title: "Unusual Activity Detector",
    slug: "unusual-activity",
    description:
      "Spot trading-volume spikes far above a stock's recent average, and cross-reference news to tell explained moves from quiet accumulation.",
    href: "/investor-tools/unusual-activity",
    badge: "Market Intel",
    icon: "M3 12h4l3 8 4-16 3 8h4",
    available: true,
    group: "quality",
  },
  {
    title: "Catalyst Impact Analyzer",
    slug: "catalyst-impact",
    description:
      "Event study: see how each type of news — drill results, financings, resource updates — has historically moved a company's share price.",
    href: "/investor-tools/catalyst-impact",
    badge: "Event Study",
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
    available: true,
    group: "quality",
  },
  {
    title: "Project Due-Diligence Assistant",
    slug: "due-diligence",
    description:
      "Ask a due-diligence question about a company and get the exact NI 43-101 report passages that answer it — ranked by relevance, with citations.",
    href: "/investor-tools/due-diligence",
    badge: "Due Diligence",
    icon: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
    available: true,
    group: "diligence",
  },
  {
    title: "Resource Grade Ranker",
    slug: "grade-ranker",
    description:
      "Rank all companies by resource grade and size. Filter by commodity, stage, and minimum resource. Find the highest-grade deposits at a glance.",
    href: "/investor-tools/grade-ranker",
    badge: "Screener",
    icon: "M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12",
    available: true,
    group: "screen",
  },
  {
    title: "Peer Comparison Engine",
    slug: "peer-comparison",
    description:
      "Compare any company against auto-detected peers on EV/oz, P/NAV, grade, AISC, and financing history. Find mispriced opportunities.",
    href: "/investor-tools/peer-comparison",
    badge: "Analysis",
    icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
    available: true,
    group: "value",
  },
  {
    title: "Financing Flow Tracker",
    slug: "financing-flow",
    description:
      "Track where capital is flowing in junior mining. Monthly trends, by commodity, by type. Spot smart money before the crowd.",
    href: "/investor-tools/financing-flow",
    badge: "Market Intel",
    icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    available: true,
    group: "screen",
  },
  {
    title: "Sector Pulse Dashboard",
    slug: "sector-pulse",
    description:
      "Real-time sector overview: metals prices, market breadth, top gainers/losers, financing activity, and news volume.",
    href: "/investor-tools/sector-pulse",
    badge: "Dashboard",
    icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
    available: true,
    group: "screen",
  },
  {
    title: "NI 43-101 Report Analyzer",
    slug: "ni43-101-analyzer",
    description:
      "AI-powered analysis of technical reports. Get structured summaries, compare NPV vs market cap, and extract key data points.",
    href: "/investor-tools/ni43-101-analyzer",
    badge: "AI",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    available: true,
    group: "value",
  },
  {
    title: "Drill Result Scanner",
    slug: "drill-scanner",
    description:
      "Search press releases for drill results across all companies. Find the most active drillers and track exploration news by commodity.",
    href: "/investor-tools/drill-scanner",
    badge: "Screener",
    icon: "M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z",
    available: true,
    group: "screen",
  },
  {
    title: "News Catalyst Calendar",
    slug: "catalyst-calendar",
    description:
      "Track news release frequency by company. Spot quiet companies, find the most active newsmakers, and monitor weekly volume trends.",
    href: "/investor-tools/catalyst-calendar",
    badge: "Market Intel",
    icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
    available: true,
    group: "quality",
  },
  {
    title: "Insider Activity Dashboard",
    slug: "insider-activity",
    description:
      "Track management buying and selling from SEDI filings. Detect cluster buying — the strongest signal in junior mining.",
    href: "#",
    badge: "Coming Soon",
    icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z",
    available: false,
    group: null,
  },
  {
    title: "Property Valuation Tool",
    slug: "property-valuation",
    description:
      "Compare property listings with $/hectare benchmarks by mineral and jurisdiction. Find undervalued exploration properties.",
    href: "/investor-tools/property-valuation",
    badge: "Marketplace",
    icon: "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z",
    available: true,
    group: "diligence",
  },
  {
    title: "Portfolio X-Ray",
    slug: "portfolio-xray",
    description:
      "Analyze a set of companies for commodity exposure, geographic concentration, stage diversification, and dilution risk.",
    href: "/investor-tools/portfolio-xray",
    badge: "Portfolio",
    icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
    available: true,
    group: "diligence",
  },
];

/** Derived so the copy can't drift out of step with the grid. */
export const AVAILABLE_COUNT = TOOLS.filter((t) => t.available).length;

/** Prospector unlocks everything except the Miner-only tools. */
export const PROSPECTOR_COUNT = AVAILABLE_COUNT - MINER_TOOL_SLUGS.length;

/**
 * The five stages of evaluating a junior, in the order an analyst works
 * through them. Each becomes an <h2> with real prose — the index page had a
 * flat card grid and no headings at all, which gave Google no structure to
 * read and left ~550 words on a page competing for a category-level query.
 */
export const TOOL_GROUPS: {
  id: ToolGroupId;
  heading: string;
  blurb: string;
}[] = [
  {
    id: "screen",
    heading: "Screen and discover",
    blurb:
      "Start by narrowing the field. There are hundreds of listed juniors and most will never build a mine, so the first job is finding the handful worth an afternoon of reading. Rank by resource grade and size, search drill results across every company at once, follow where financing capital is actually moving, and read the sector's temperature before you commit to a thesis.",
  },
  {
    id: "value",
    heading: "Value and compare",
    blurb:
      "A junior is only cheap or expensive relative to something. These tools supply the comparison: contained ounces against market capitalisation, market capitalisation against a technical report's NPV, a share price against its peers, and a stock's moves against the metal underneath it. Resource growth over successive technical reports shows whether management is actually adding ounces or restating the same ones.",
  },
  {
    id: "capital",
    heading: "Read the capital structure",
    blurb:
      "Exploration is funded by issuing shares, so the capital structure is where junior mining returns are quietly made and lost. A discovery can be entirely offset by the dilution that paid for it. These tools show the shares already issued, the warrants still outstanding, the price at which that overhang becomes exercisable, and when it expires.",
  },
  {
    id: "quality",
    heading: "Judge quality and risk",
    blurb:
      "Two risks dominate junior mining and neither appears on a conventional screener: you may not be able to sell, and the company may not be doing anything. These tools measure both directly — how many days it would take to exit a position at realistic volume, and what share of a company's announcements report an actual result rather than corporate housekeeping.",
  },
  {
    id: "diligence",
    heading: "Diligence and portfolio",
    blurb:
      "Once a name survives screening, the work turns to reading technical reports and understanding what you already own. Ask a question and get the exact NI 43-101 passages that answer it, benchmark a property against dollar-per-hectare comparables, and check a whole portfolio for the concentration risk that builds up when every position is the same commodity in the same jurisdiction.",
  },
];

/** Search-intent phrasing mapped to the tool that answers it. */
export const QUESTION_MAP: {
  question: string;
  slugs: string[];
  answer: string;
}[] = [
  {
    question: "Am I about to be diluted?",
    slugs: ["warrant-radar", "dilution-tracker"],
    answer:
      "Check the warrants outstanding, the strike price that makes them exercisable, and how much the share count has already grown across previous raises.",
  },
  {
    question: "Could I actually sell this position?",
    slugs: ["liquidity-screener"],
    answer:
      "Enter your position size and see the days-to-exit at a realistic share of daily volume. On thin listings the answer is often measured in weeks.",
  },
  {
    question: "Is this company exploring, or just promoting?",
    slugs: ["signal-to-noise"],
    answer:
      "Compare the share of announcements that report drill results, resource updates or studies against the sector norm.",
  },
  {
    question: "Is it cheap compared with its peers?",
    slugs: ["peer-comparison"],
    answer:
      "Benchmark market capitalisation per contained ounce, price to NPV, grade and AISC against automatically detected comparables.",
  },
  {
    question: "Do I get real leverage to the metal price?",
    slugs: ["metal-correlation"],
    answer:
      "Measure correlation, beta and R² against the underlying commodity. A beta above 1 means the stock has historically amplified the metal's moves.",
  },
  {
    question: "Has the resource actually grown, or just been restated?",
    slugs: ["resource-growth"],
    answer:
      "Track contained ounces, grade and tonnage across successive NI 43-101 reports to separate genuine additions from reclassification.",
  },
  {
    question: "Why did this stock move today?",
    slugs: ["unusual-activity", "catalyst-impact"],
    answer:
      "Find volume spikes above the recent average and cross-reference news, then see how that category of announcement has historically moved the price.",
  },
  {
    question: "What does the technical report actually say?",
    slugs: ["due-diligence", "ni43-101-analyzer"],
    answer:
      "Ask a plain-language question and get the specific report passages that answer it, with citations, alongside a structured summary.",
  },
];

export function toolBySlug(slug: string): Tool | undefined {
  return TOOLS.find((t) => t.slug === slug);
}
