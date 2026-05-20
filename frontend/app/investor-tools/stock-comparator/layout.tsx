import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/stock-comparator";
const description =
  "Compare the share-price performance of multiple junior mining companies side by side. Normalized % return curves, rankings, and volatility over any window.";

export const metadata: Metadata = {
  title: "Stock Performance Comparator - Junior Mining Intelligence",
  description,
  keywords: [
    "mining stock comparison",
    "compare mining stocks",
    "junior mining performance",
    "stock return chart",
    "gold stock comparison",
  ],
  openGraph: {
    title: "Stock Performance Comparator - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Stock Performance Comparator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Stock Performance Comparator - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function StockComparatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
