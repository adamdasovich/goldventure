import { Metadata } from "next";
import { PROSPECTOR_COUNT } from "@/app/investor-tools/tools";

const url = "https://juniorminingintelligence.com/pricing";

// This is the text Google shows under the result, and it was the last place on
// the site still advertising historical data and API access — neither of which
// exists — alongside a tool count of 10 that had been wrong for months. Kept
// free of prices so it cannot drift from Stripe; the count is derived.
const description =
  `Compare Junior Mining Intelligence plans. Explorer is free: 5 AI research ` +
  `questions a day, the full company directory and the news feed. Prospector ` +
  `adds unlimited AI chat, ${PROSPECTOR_COUNT} investor tools, every open ` +
  `financing round and CSV export.`;

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
