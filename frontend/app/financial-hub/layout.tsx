import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Financial Hub - Mining Investment & Accredited Investor Portal',
  description: 'Access mining company financing rounds, private placements, and investment opportunities. Complete accredited investor qualification and participate in junior mining offerings.',
  keywords: [
    'mining investments',
    'private placements',
    'accredited investor',
    'mining financing',
    'junior mining investment',
    'gold mining stocks',
    'mining crowdfunding',
    'mining share offerings',
    'Canadian mining investment'
  ],
  openGraph: {
    title: 'Financial Hub | Junior Gold Mining Intelligence',
    description: 'Access financing rounds, private placements, and investment opportunities in junior mining companies.',
    url: 'https://juniorminingintelligence.com/financial-hub',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Mining Investment Financial Hub',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Mining Investment Financial Hub',
    description: 'Access junior mining investment opportunities and financing rounds.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/financial-hub',
  },
};

export default function FinancialHubLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
