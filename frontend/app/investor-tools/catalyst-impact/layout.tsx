import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/catalyst-impact";
const description =
  "Event study for junior mining stocks: see how each type of news — drill results, financings, resource updates — has historically moved a company's share price.";

export const metadata: Metadata = {
  title: "Catalyst Impact Analyzer - Junior Mining Intelligence",
  description,
  keywords: [
    "mining news impact",
    "drill result stock reaction",
    "catalyst event study",
    "junior mining share price catalyst",
    "news driven price moves",
  ],
  openGraph: {
    title: "Catalyst Impact Analyzer - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Catalyst Impact Analyzer",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Catalyst Impact Analyzer - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function CatalystImpactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
