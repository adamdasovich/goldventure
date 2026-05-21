"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import UpgradeModal from "@/components/UpgradeModal";
import { useAuth } from "@/contexts/AuthContext";

const FREE_TOOL_SLUGS = ["grade-ranker", "sector-pulse"];

const TOOLS = [
  {
    title: "Stock Performance Comparator",
    slug: "stock-comparator",
    description:
      "Compare the share-price performance of up to 10 companies side by side. Normalized return curves, rankings, and volatility over any window.",
    href: "/investor-tools/stock-comparator",
    badge: "Analysis",
    icon: "M3 3v18h18M18.5 9.5l-5 5-3-3-4 4",
    available: true,
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
  },
];

export default function InvestorToolsPage() {
  const { subscription } = useAuth();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const tier = subscription?.effective_tier || "explorer";
  const hasFullAccess = tier === "prospector" || tier === "miner";

  const isToolFree = (slug: string) => FREE_TOOL_SLUGS.includes(slug);

  const handleToolClick = (
    e: React.MouseEvent,
    tool: (typeof TOOLS)[number],
  ) => {
    if (!tool.available) return;
    if (!hasFullAccess && !isToolFree(tool.slug)) {
      e.preventDefault();
      setShowUpgrade(true);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {showUpgrade && (
        <UpgradeModal
          onClose={() => setShowUpgrade(false)}
          feature="All 16 Investor Tools"
          requiredTier="prospector"
        />
      )}

      {/* Nav */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/companies">
                <Button variant="ghost" size="sm">
                  Companies
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm">
                  Dashboard
                </Button>
              </Link>
              <Link href="/">
                <Button variant="ghost" size="sm">
                  Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Investor Intelligence
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold text-gradient-gold mb-4">
            Investor Tools
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Purpose-built analytics for junior mining investors. Screen,
            compare, and analyze 500+ companies with data-driven tools.
          </p>
          {!hasFullAccess && (
            <div className="mt-4">
              <Link href="/pricing">
                <Badge
                  variant="slate"
                  className="cursor-pointer hover:border-gold-400/50"
                >
                  Free tier: 2 tools &middot; Upgrade for all 16
                </Badge>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Tools Grid */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {TOOLS.map((tool, i) => {
              const isFree = isToolFree(tool.slug);
              const isLocked = !hasFullAccess && !isFree && tool.available;

              return (
                <Link
                  key={i}
                  href={tool.available ? tool.href : "#"}
                  onClick={(e) => handleToolClick(e, tool)}
                  className={`group block ${!tool.available ? "pointer-events-none opacity-60" : ""}`}
                >
                  <div
                    className={`glass-card rounded-xl p-5 h-full flex flex-col transition-all hover:border-gold-400/30 ${isLocked ? "relative" : ""}`}
                  >
                    {/* Lock overlay for premium tools */}
                    {isLocked && (
                      <div className="absolute top-3 right-3">
                        <svg
                          className="w-4 h-4 text-slate-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    )}

                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gold-500/15 border border-gold-500/30 group-hover:scale-110 transition-transform">
                        <svg
                          className="w-5 h-5 text-gold-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d={tool.icon}
                          />
                        </svg>
                      </div>
                      <Badge
                        variant={tool.available ? "gold" : "slate"}
                        className="text-[10px]"
                      >
                        {tool.badge}
                      </Badge>
                    </div>

                    {/* Content */}
                    <h3 className="text-lg font-semibold text-slate-200 group-hover:text-gold-400 transition-colors mb-2">
                      {tool.title}
                    </h3>
                    <p className="text-sm text-slate-400 leading-relaxed flex-1">
                      {tool.description}
                    </p>

                    {/* CTA */}
                    {tool.available && (
                      <div className="mt-4 pt-3 border-t border-slate-700/50">
                        <span className="text-sm text-gold-400 font-medium group-hover:underline">
                          {isLocked ? "Upgrade to Access →" : "Launch Tool →"}
                        </span>
                      </div>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
