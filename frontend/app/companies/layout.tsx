import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Junior Gold Mining Companies - Explore TSXV & TSX Mining Stocks',
  description: 'Browse our comprehensive database of junior gold mining companies listed on TSXV and TSX. View resource estimates, project data, and investment opportunities in gold exploration.',
  keywords: [
    'junior gold mining companies',
    'TSXV mining stocks',
    'TSX gold companies',
    'gold exploration companies',
    'mining stock database',
    'gold mining investments',
    'Canadian mining companies',
    'gold resource estimates',
    'mining company analysis'
  ],
  openGraph: {
    title: 'Junior Gold Mining Companies | Junior Gold Mining Intelligence',
    description: 'Comprehensive database of junior gold mining companies with detailed resource estimates and project data.',
    url: 'https://juniorgoldminingintelligence.com/companies',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Junior Gold Mining Companies Database',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Junior Gold Mining Companies',
    description: 'Browse junior gold mining companies with AI-powered analysis.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://juniorgoldminingintelligence.com/companies',
  },
};

export default function CompaniesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
