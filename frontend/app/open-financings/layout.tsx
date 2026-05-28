import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Open Financings - Active Junior Mining Capital Raises",
  description:
    "Browse open financing rounds from junior mining companies — private placements, bought deals, and flow-through offerings currently raising capital across TSXV and TSX.",
  keywords: [
    "open financings",
    "active mining financings",
    "junior mining capital raises",
    "private placements open",
    "TSXV financings open",
    "flow-through shares",
    "bought deals",
    "current mining fundraising",
  ],
  openGraph: {
    title: "Open Financings - Active Junior Mining Capital Raises",
    description:
      "Browse open financing rounds from junior mining companies currently raising capital.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/open-financings",
  },
  twitter: {
    card: "summary_large_image",
    title: "Open Financings - Active Junior Mining Capital Raises",
    description: "Browse open financing rounds currently raising capital.",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/open-financings",
  },
};

export default function OpenFinancingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
