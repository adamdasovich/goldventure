import { Metadata } from 'next';
import PropertyDetailClient from './PropertyDetailClient';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getProperty(slug: string) {
  try {
    const response = await fetch(`${API_URL}/properties/listings/${slug}/`, {
      cache: 'no-store'
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch property for metadata:', error);
    return null;
  }
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const property = await getProperty(params.slug);

  if (!property) {
    return {
      title: 'Property Not Found',
      description: 'The requested property listing could not be found.',
    };
  }

  const formatPrice = (price: number | null, currency: string) => {
    if (!price) return 'Contact for Price';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'CAD',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const title = `${property.title} - ${property.province_state}, ${property.country_display}`;
  const description = property.summary || property.description?.slice(0, 155) ||
    `${property.listing_type.replace('_', ' ')} property in ${property.province_state}, ${property.country_display}. ${property.total_hectares || 'N/A'} hectares, ${property.primary_mineral_display || 'mineral exploration'} project.`;

  const images = property.hero_image
    ? [`https://juniorgoldminingintelligence.com${property.hero_image}`]
    : property.media?.[0]?.file_url
    ? [`https://juniorgoldminingintelligence.com${property.media[0].file_url}`]
    : ['/og-image.png'];

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: 'article',
      images,
      url: `https://juniorgoldminingintelligence.com/properties/${params.slug}`,
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images,
    },
    alternates: {
      canonical: `https://juniorgoldminingintelligence.com/properties/${params.slug}`,
    },
  };
}

export default function PropertyDetailPage() {
  return <PropertyDetailClient />;
}
