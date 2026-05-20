import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/investor-tools/sector-pulse";
const description =
  "Real-time junior mining sector overview: metals prices, market breadth, top gainers and losers, financing activity, and news volume in one dashboard.";

export const metadata: Metadata = {
  title: "Sector Pulse Dashboard - Junior Mining Market Overview",
  description,
  keywords: [
    "mining sector dashboard",
    "junior mining market overview",
    "metals prices dashboard",
    "mining market breadth",
    "mining gainers and losers",
  ],
  openGraph: {
    title:
      "Sector Pulse Dashboard - Junior Mining Market Overview | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Sector Pulse Dashboard",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Sector Pulse Dashboard - Junior Mining Market Overview",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function SectorPulseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
