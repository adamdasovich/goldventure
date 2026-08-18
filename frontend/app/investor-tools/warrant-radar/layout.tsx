import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/investor-tools/warrant-radar";
const description =
  "Track warrant overhang across junior mining financings. See which tranches are in the money, when they expire, strike prices, and estimated dilution if exercised.";

export const metadata: Metadata = {
  title: "Warrant Overhang Radar - Junior Mining Dilution Tracker",
  description,
  keywords: [
    "warrant overhang",
    "mining warrant expiry",
    "junior mining dilution",
    "in the money warrants",
    "private placement warrants",
    "warrant strike price",
  ],
  openGraph: {
    title:
      "Warrant Overhang Radar - Junior Mining Dilution Tracker | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Warrant Overhang Radar",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Warrant Overhang Radar - Junior Mining Dilution Tracker",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function WarrantRadarLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
