import type { Metadata } from "next";

export const metadata: Metadata = {
  title:
    "Prospector's Property Exchange - Mining Claims & Mineral Properties For Sale",
  description:
    "Browse mineral claims, exploration properties, and mining development projects for sale. Connect directly with prospectors and list your properties for free.",
  keywords: [
    "mining claims for sale",
    "mineral properties",
    "gold claims",
    "exploration properties",
    "mining land for sale",
    "prospector exchange",
    "Canadian mining claims",
    "mineral rights",
    "gold mining property",
    "placer claims",
  ],
  openGraph: {
    title: "Prospector's Property Exchange | Junior Gold Mining Intelligence",
    description:
      "Browse and list mineral claims, exploration properties, and mining projects. Free listings for prospectors.",
    url: "https://juniorminingintelligence.com/properties",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Prospector's Property Exchange",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Prospector's Property Exchange",
    description: "Browse mineral claims and mining properties for sale.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/properties",
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
      name: "Prospector's Exchange",
      item: "https://juniorminingintelligence.com/properties",
    },
  ],
};

export default function PropertiesLayout({
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
