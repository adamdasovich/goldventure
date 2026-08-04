import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gold & Precious Metals Prices - Live Gold, Silver, Platinum Charts",
  description:
    "Track real-time gold, silver, platinum, and palladium prices. View historical price charts, market analysis, and precious metals trends for mining investors.",
  openGraph: {
    title: "Live Precious Metals Prices | Junior Gold Mining Intelligence",
    description:
      "Real-time gold, silver, platinum and palladium prices with historical charts and market analysis.",
    url: "https://juniorminingintelligence.com/metals",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Live Precious Metals Prices",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Live Gold & Precious Metals Prices",
    description:
      "Track real-time precious metals prices with charts and analysis.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/metals",
  },
};

const breadcrumbJsonLd = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    {
      "@type": "ListItem",
      position: 1,
      name: "Home",
      item: "https://juniorminingintelligence.com",
    },
    {
      "@type": "ListItem",
      position: 2,
      name: "Metals Prices",
      item: "https://juniorminingintelligence.com/metals",
    },
  ],
};

export default function MetalsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      {children}
    </>
  );
}
