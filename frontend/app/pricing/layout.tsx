import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/pricing";
const description =
  "Compare Junior Mining Intelligence plans. Start free with the Explorer tier, or upgrade to Prospector or Miner for unlimited AI research, all 10 investor tools, historical data, and API access.";

export const metadata: Metadata = {
  title: "Pricing & Subscription Plans",
  description,
  keywords: [
    "junior mining intelligence pricing",
    "mining research subscription",
    "mining stock screener pricing",
    "mining data plans",
    "investor tools subscription",
  ],
  openGraph: {
    title:
      "Pricing - Junior Mining Intelligence Plans & Subscriptions | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Junior Mining Intelligence Pricing",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing - Junior Mining Intelligence Plans & Subscriptions",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
