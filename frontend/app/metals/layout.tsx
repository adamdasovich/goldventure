import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Gold & Precious Metals Prices - Live Gold, Silver, Platinum Charts',
  description: 'Track real-time gold, silver, platinum, and palladium prices. View historical price charts, market analysis, and precious metals trends for mining investors.',
  keywords: [
    'gold price today',
    'live gold price',
    'silver price',
    'platinum price',
    'palladium price',
    'precious metals prices',
    'gold price chart',
    'gold spot price',
    'XAU USD',
    'precious metals market',
    'gold investment'
  ],
  openGraph: {
    title: 'Live Precious Metals Prices | Junior Gold Mining Intelligence',
    description: 'Real-time gold, silver, platinum and palladium prices with historical charts and market analysis.',
    url: 'https://juniorminingintelligence.com/metals',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Live Precious Metals Prices',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Live Gold & Precious Metals Prices',
    description: 'Track real-time precious metals prices with charts and analysis.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/metals',
  },
};

export default function MetalsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
