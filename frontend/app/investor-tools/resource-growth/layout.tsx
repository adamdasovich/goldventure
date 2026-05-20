import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/resource-growth";
const description =
  "Track how a junior mining company's mineral resource estimates have grown over time — contained ounces, grade and tonnage across successive NI 43-101 reports.";

export const metadata: Metadata = {
  title: "Resource Growth Tracker - Junior Mining Intelligence",
  description,
  keywords: [
    "mineral resource growth",
    "NI 43-101 resource history",
    "gold resource estimate trend",
    "mining resource expansion",
    "contained ounces growth",
  ],
  openGraph: {
    title: "Resource Growth Tracker - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Resource Growth Tracker",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Resource Growth Tracker - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function ResourceGrowthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
