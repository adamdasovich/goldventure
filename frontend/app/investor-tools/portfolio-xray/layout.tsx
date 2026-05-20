import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/portfolio-xray";
const description =
  "Analyze your junior mining portfolio for commodity exposure, geographic concentration, stage diversification, and dilution risk in one report.";

export const metadata: Metadata = {
  title: "Portfolio X-Ray - Junior Mining Portfolio Analysis",
  description,
  keywords: [
    "mining portfolio analysis",
    "commodity exposure",
    "dilution risk",
    "portfolio diversification",
    "junior mining portfolio",
  ],
  openGraph: {
    title:
      "Portfolio X-Ray - Junior Mining Portfolio Analysis | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Portfolio X-Ray",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Portfolio X-Ray - Junior Mining Portfolio Analysis",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function PortfolioXrayLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
