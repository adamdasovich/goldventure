import { Metadata } from "next";

export const metadata: Metadata = {
  title:
    "Investor Tools - Junior Mining Screeners, Analyzers & Portfolio Analytics",
  description:
    "Purpose-built analytics for junior mining investors. Screen companies by resource grade, compare peers on EV/oz and P/NAV, track financing flows, analyze NI 43-101 reports, and scan drill results across 500+ companies.",
  keywords: [
    "junior mining screener",
    "mining stock screener",
    "peer comparison mining",
    "NI 43-101 analyzer",
    "drill result scanner",
    "mining financing tracker",
    "resource grade ranker",
    "mining portfolio analysis",
    "EV per ounce",
    "mining sector dashboard",
    "property valuation mining",
    "catalyst calendar mining",
  ],
  openGraph: {
    title:
      "Investor Tools - Junior Mining Screeners & Analytics | Junior Mining Intelligence",
    description:
      "Purpose-built analytics for junior mining investors. Screen, compare, and analyze 500+ companies with data-driven tools.",
    type: "website",
    url: "https://juniorminingintelligence.com/investor-tools",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Junior Mining Investor Tools",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Junior Mining Investor Tools - Screeners & Analytics",
    description:
      "Screen companies by grade, compare peers, track financing flows, and analyze NI 43-101 reports across 500+ junior mining companies.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/investor-tools",
  },
};

export default function InvestorToolsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
