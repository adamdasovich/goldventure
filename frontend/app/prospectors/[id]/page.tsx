import { Metadata } from "next";
import { notFound } from "next/navigation";
import ProspectorProfileClient from "./ProspectorProfileClient";

const API_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

async function getProspector(id: string) {
  try {
    const response = await fetch(`${API_URL}/properties/prospectors/${id}/`, {
      next: { revalidate: 1800 },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const prospector = await getProspector(id);

  if (!prospector) {
    return {
      title: "Prospector Not Found",
    };
  }

  const name = prospector.display_name || prospector.username;
  const title = `${name} - Prospector Profile | Prospector's Exchange`;
  const description =
    prospector.bio?.slice(0, 155) ||
    `${name} is a prospector on Junior Mining Intelligence with ${prospector.active_listings || 0} active property listings.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "profile",
      url: `https://juniorminingintelligence.com/prospectors/${id}`,
    },
    alternates: {
      canonical: `https://juniorminingintelligence.com/prospectors/${id}`,
    },
  };
}

export default async function ProspectorProfilePage({ params }: Props) {
  const { id } = await params;
  const prospector = await getProspector(id);

  if (!prospector) {
    notFound();
  }

  const name = prospector.display_name || prospector.username;
  const canonicalUrl = `https://juniorminingintelligence.com/prospectors/${id}`;

  const personJsonLd = {
    "@context": "https://schema.org",
    "@type": "Person",
    name,
    url: canonicalUrl,
    ...(prospector.bio && { description: prospector.bio.slice(0, 280) }),
    ...(prospector.profile_photo_url && {
      image: prospector.profile_photo_url.startsWith("http")
        ? prospector.profile_photo_url
        : `https://juniorminingintelligence.com${prospector.profile_photo_url}`,
    }),
    jobTitle: "Mineral Prospector",
    worksFor: {
      "@type": "Organization",
      name: "Junior Mining Intelligence Prospector's Exchange",
      url: "https://juniorminingintelligence.com/properties",
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
      { "@type": "ListItem", position: 3, name, item: canonicalUrl },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(personJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <ProspectorProfileClient params={params} />
    </>
  );
}
