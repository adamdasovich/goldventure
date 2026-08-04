import { Metadata } from "next";

export const metadata: Metadata = {
  title:
    "Junior Mining Glossary - Gold, Silver, Lithium, REE & Critical Minerals Terms",
  description:
    "Comprehensive glossary of 100+ mining terms including gold, silver, lithium, rare earths, battery metals, critical minerals, NI 43-101 standards, TSXV definitions, resource classifications, and investment concepts.",
  openGraph: {
    title:
      "Junior Mining Glossary - Gold, Silver, Lithium, REE & Critical Minerals",
    description:
      "100+ mining terms covering gold, silver, lithium, rare earths, battery metals, critical minerals, NI 43-101 standards, and investment concepts.",
    type: "website",
    url: "https://juniorminingintelligence.com/glossary",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/glossary",
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
      name: "Glossary",
      item: "https://juniorminingintelligence.com/glossary",
    },
  ],
};

export default function GlossaryLayout({
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
