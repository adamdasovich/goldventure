import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/property-valuation";
const description =
  "Compare mining property listings with $/hectare benchmarks by mineral and jurisdiction. Find undervalued exploration properties on the marketplace.";

export const metadata: Metadata = {
  title: "Property Valuation Tool - Mining Property Benchmarks",
  description,
  keywords: [
    "mining property valuation",
    "property per hectare",
    "exploration property pricing",
    "mining claim valuation",
    "undervalued mining properties",
  ],
  openGraph: {
    title:
      "Property Valuation Tool - Mining Property Benchmarks | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Property Valuation Tool",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Property Valuation Tool - Mining Property Benchmarks",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function PropertyValuationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
