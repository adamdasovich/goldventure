import { Metadata } from "next";
import { notFound } from "next/navigation";
import PropertyDetailClient from "./PropertyDetailClient";

const API_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

async function getProperty(slug: string) {
  const fetchUrl = `${API_URL}/properties/listings/${slug}/`;

  try {
    const response = await fetch(fetchUrl, {
      next: { revalidate: 1800 },
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch property:", error);
    return null;
  }
}

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const property = await getProperty(slug);

  if (!property) {
    return {
      title: "Property Not Found",
      description: "The requested property listing could not be found.",
      robots: { index: false, follow: false },
    };
  }

  const title = `${property.title} - ${property.province_state}, ${property.country_display}`;
  const description =
    property.summary ||
    property.description?.slice(0, 155) ||
    `${(property.listing_type || "").replace("_", " ")} property in ${property.province_state}, ${property.country_display}. ${property.total_hectares || "N/A"} hectares, ${property.primary_mineral_display || "mineral exploration"} project.`;

  // Prefer the listing's own hero image; fall back to a dynamic, branded
  // OG card that includes title, mineral, location, and acreage.
  const images = property.hero_image
    ? [`https://juniorminingintelligence.com${property.hero_image}`]
    : property.media?.[0]?.file_url
      ? [`https://juniorminingintelligence.com${property.media[0].file_url}`]
      : [`/og/property/${slug}`];

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "article",
      images,
      url: `https://juniorminingintelligence.com/properties/${slug}`,
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images,
    },
    alternates: {
      canonical: `https://juniorminingintelligence.com/properties/${slug}`,
    },
  };
}

export const revalidate = 1800; // ISR: refresh every 30 minutes

export default async function PropertyDetailPage({ params }: Props) {
  const { slug } = await params;
  const property = await getProperty(slug);

  if (!property) notFound();

  const canonicalUrl = `https://juniorminingintelligence.com/properties/${slug}`;
  const heroImageUrl = property.hero_image
    ? `https://juniorminingintelligence.com${property.hero_image}`
    : property.media?.[0]?.file_url
      ? `https://juniorminingintelligence.com${property.media[0].file_url}`
      : undefined;

  const productJsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: property.title,
    description:
      property.summary || property.description?.slice(0, 300) || property.title,
    ...(heroImageUrl && { image: [heroImageUrl] }),
    category:
      property.primary_mineral_display || "Mineral Exploration Property",
    ...(property.asking_price && {
      offers: {
        "@type": "Offer",
        price: property.asking_price,
        priceCurrency: property.currency || "USD",
        availability:
          property.status === "active"
            ? "https://schema.org/InStock"
            : "https://schema.org/SoldOut",
        url: canonicalUrl,
      },
    }),
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
      {
        "@type": "ListItem",
        position: 3,
        name: property.title,
        item: canonicalUrl,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(productJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <PropertyDetailClient initialListing={property} />
    </>
  );
}
