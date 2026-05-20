import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/ni43-101-analyzer";
const description =
  "AI-powered analysis of NI 43-101 technical reports. Get structured summaries, compare NPV against market cap, and extract key resource data points instantly.";

export const metadata: Metadata = {
  title: "NI 43-101 Report Analyzer - AI Technical Report Analysis",
  description,
  keywords: [
    "NI 43-101 analyzer",
    "technical report analysis",
    "mining NPV analysis",
    "resource estimate analysis",
    "AI mining reports",
  ],
  openGraph: {
    title:
      "NI 43-101 Report Analyzer - AI Technical Report Analysis | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "NI 43-101 Report Analyzer",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "NI 43-101 Report Analyzer - AI Technical Report Analysis",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function Ni43101AnalyzerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
