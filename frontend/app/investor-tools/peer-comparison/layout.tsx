import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/peer-comparison";
const description =
  "Compare any junior mining company against auto-detected peers on EV/oz, P/NAV, grade, AISC, and financing history. Find mispriced mining opportunities.";

export const metadata: Metadata = {
  title: "Peer Comparison Engine - Compare Junior Mining Stocks",
  description,
  keywords: [
    "mining peer comparison",
    "EV per ounce",
    "P/NAV mining",
    "junior mining valuation",
    "AISC comparison",
  ],
  openGraph: {
    title:
      "Peer Comparison Engine - Compare Junior Mining Stocks | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Peer Comparison Engine",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Peer Comparison Engine - Compare Junior Mining Stocks",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function PeerComparisonLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
