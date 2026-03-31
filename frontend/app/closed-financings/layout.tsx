import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Closed Financings - Recent Junior Mining Fundraising Rounds",
  description:
    "Track recently closed financings and capital raises by junior mining companies. Private placements, bought deals, and flow-through share offerings across TSXV and TSX-listed explorers.",
  keywords: [
    "closed financings",
    "junior mining financings",
    "private placements",
    "mining capital raises",
    "TSXV financings",
    "flow-through shares",
    "bought deals",
    "mining fundraising",
  ],
  openGraph: {
    title: "Closed Financings - Junior Mining Capital Raises",
    description:
      "Track recently closed financings by junior mining companies. Private placements, bought deals, and flow-through offerings.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/closed-financings",
  },
  twitter: {
    card: "summary_large_image",
    title: "Closed Financings - Junior Mining Capital Raises",
    description: "Track recently closed financings by junior mining companies.",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/closed-financings",
  },
};

export default function ClosedFinancingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
