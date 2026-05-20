import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/financing-flow";
const description =
  "Track where capital is flowing in junior mining. Monthly financing trends by commodity and deal type. Spot smart money moving into gold, silver, and lithium.";

export const metadata: Metadata = {
  title: "Financing Flow Tracker - Junior Mining Capital Trends",
  description,
  keywords: [
    "mining financing tracker",
    "junior mining capital flows",
    "private placement trends",
    "mining deal activity",
    "exploration funding",
  ],
  openGraph: {
    title:
      "Financing Flow Tracker - Junior Mining Capital Trends | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Financing Flow Tracker",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Financing Flow Tracker - Junior Mining Capital Trends",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function FinancingFlowLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
