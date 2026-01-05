import type { Metadata } from 'next';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

type Props = {
  params: Promise<{ id: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;

  try {
    // Fetch company data for metadata
    const response = await fetch(`${API_BASE_URL}/companies/${id}/`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      return {
        title: 'Company Not Found',
      };
    }

    const company = await response.json();

    const title = `${company.name} (${company.ticker_symbol}) - Gold Mining Company Analysis`;
    const description = company.description
      ? `${company.description.substring(0, 155)}...`
      : `Detailed analysis of ${company.name} (${company.exchange}: ${company.ticker_symbol}). Explore projects, resource estimates, financings, and real-time news for this junior gold mining company.`;

    return {
      title,
      description,
      keywords: [
        company.name,
        company.ticker_symbol,
        `${company.exchange} ${company.ticker_symbol}`,
        'gold mining stock',
        'junior mining company',
        'mineral exploration',
        'mining investment',
        company.headquarters || '',
      ].filter(Boolean),
      openGraph: {
        title,
        description,
        type: 'website',
        url: `https://juniorminingintelligence.com/companies/${id}`,
        siteName: 'Junior Gold Mining Intelligence',
        images: [
          {
            url: '/og-image.png',
            width: 1200,
            height: 630,
            alt: `${company.name} Company Profile`,
          },
        ],
      },
      twitter: {
        card: 'summary_large_image',
        title,
        description,
        images: ['/og-image.png'],
      },
      alternates: {
        canonical: `https://juniorminingintelligence.com/companies/${id}`,
      },
    };
  } catch (error) {
    console.error('Error generating metadata:', error);
    return {
      title: 'Company Profile',
    };
  }
}

export default function CompanyLayout({ children }: Props) {
  return <>{children}</>;
}
