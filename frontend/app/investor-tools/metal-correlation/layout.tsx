import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/metal-correlation";
const description =
  "Measure how closely junior mining stocks track their underlying metal. Correlation and beta against gold, silver, copper, and other commodity prices over time.";

export const metadata: Metadata = {
  title: "Metal Leverage Analyzer - Mining Stock vs Metal Price Correlation",
  description,
  keywords: [
    "mining stock correlation",
    "gold stock beta",
    "metal price leverage",
    "mining stock vs gold price",
    "commodity correlation analysis",
    "junior mining beta",
  ],
  openGraph: {
    title:
      "Metal Leverage Analyzer - Mining Stock vs Metal Price Correlation | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Metal Leverage Analyzer",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Metal Leverage Analyzer - Mining Stock vs Metal Price Correlation",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function MetalCorrelationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
