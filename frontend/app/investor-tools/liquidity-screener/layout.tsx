import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/liquidity-screener";
const description =
  "Find out how many days it would take to sell a junior mining position. Median daily dollar volume, sellable-per-day, and days-to-exit for any position size.";

// Without this file the route inherits investor-tools/layout.tsx, including
// its canonical — which pointed this page at /investor-tools and told Google
// to drop it from the index.
export const metadata: Metadata = {
  title: "Liquidity & Days to Exit - Junior Mining Stock Liquidity Screener",
  description,
  keywords: [
    "junior mining liquidity",
    "days to exit",
    "illiquid mining stocks",
    "daily dollar volume",
    "can I sell my position",
    "thin trading mining stocks",
  ],
  openGraph: {
    title:
      "Liquidity & Days to Exit - Junior Mining Stock Liquidity Screener | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Liquidity & Days to Exit",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Liquidity & Days to Exit - Junior Mining Liquidity Screener",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function LiquidityScreenerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
