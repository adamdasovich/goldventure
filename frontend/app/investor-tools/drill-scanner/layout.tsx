import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/investor-tools/drill-scanner";
const description =
  "Search press releases for drill results across 500+ junior mining companies. Find the most active drillers and track exploration news by commodity.";

export const metadata: Metadata = {
  title: "Drill Result Scanner - Search Junior Mining Drill Results",
  description,
  keywords: [
    "drill result scanner",
    "mining drill results",
    "exploration news",
    "drill intercepts",
    "junior mining exploration",
  ],
  openGraph: {
    title:
      "Drill Result Scanner - Search Junior Mining Drill Results | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Drill Result Scanner",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Drill Result Scanner - Search Junior Mining Drill Results",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function DrillScannerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
