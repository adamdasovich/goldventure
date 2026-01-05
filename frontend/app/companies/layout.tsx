import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Junior Mining Companies - Gold, Silver & Critical Minerals | TSXV & TSX Stocks',
  description: 'Browse 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals on TSXV and TSX. View resource estimates, project data, and investment opportunities.',
  keywords: [
    'junior mining companies',
    'gold mining companies',
    'silver mining stocks',
    'lithium exploration companies',
    'critical minerals companies',
    'rare earth mining',
    'copper mining stocks',
    'TSXV mining stocks',
    'TSX mining companies',
    'battery metals companies',
    'mining stock database',
    'mineral exploration companies',
    'Canadian mining companies',
    'mining resource estimates',
    'mining company analysis'
  ],
  openGraph: {
    title: 'Junior Mining Companies: Gold, Silver & Critical Minerals | Junior Mining Intelligence',
    description: 'Comprehensive database of 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals with detailed resource estimates.',
    url: 'https://juniorminingintelligence.com/companies',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Junior Mining Companies Database',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Junior Mining Companies: Gold, Silver & Critical Minerals',
    description: 'Browse 500+ junior mining companies with AI-powered analysis. Track gold, silver, lithium, copper, rare earths & critical minerals.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/companies',
  },
};

export default function CompaniesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
