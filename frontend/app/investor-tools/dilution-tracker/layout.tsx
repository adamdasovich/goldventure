import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/dilution-tracker";
const description =
  "Track a junior mining company's share dilution history — shares issued per financing, cumulative dilution, and outstanding warrant overhang.";

export const metadata: Metadata = {
  title: "Dilution Tracker - Junior Mining Intelligence",
  description,
  keywords: [
    "mining share dilution",
    "junior mining financing history",
    "warrant overhang",
    "shares outstanding growth",
    "private placement dilution",
  ],
  openGraph: {
    title: "Dilution Tracker - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Dilution Tracker",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Dilution Tracker - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function DilutionTrackerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
