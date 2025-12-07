import type { Metadata } from 'next';
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import ClientLayout from './ClientLayout';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://juniorgoldminingintelligence.com'),
  title: {
    default: 'Junior Gold Mining Intelligence - AI-Powered Mining Investment Platform',
    template: '%s | Junior Gold Mining Intelligence'
  },
  description: 'Discover and analyze junior gold mining companies with AI-powered insights. Real-time data, resource estimates, financings, and expert analysis for gold exploration investments.',
  keywords: [
    'junior gold mining',
    'gold exploration',
    'mining stocks',
    'gold investments',
    'mineral exploration',
    'gold mining companies',
    'TSXV mining',
    'TSX mining',
    'gold resource estimates',
    'mining financings',
    'precious metals',
    'mining intelligence',
    'AI mining analysis',
    'gold mining news',
    'exploration companies'
  ],
  authors: [{ name: 'Junior Gold Mining Intelligence' }],
  creator: 'Junior Gold Mining Intelligence',
  publisher: 'Junior Gold Mining Intelligence',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://juniorgoldminingintelligence.com',
    siteName: 'Junior Gold Mining Intelligence',
    title: 'Junior Gold Mining Intelligence - AI-Powered Mining Investment Platform',
    description: 'Discover and analyze junior gold mining companies with AI-powered insights. Real-time data, resource estimates, financings, and expert analysis.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Junior Gold Mining Intelligence Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Junior Gold Mining Intelligence - AI-Powered Mining Investment Platform',
    description: 'Discover and analyze junior gold mining companies with AI-powered insights and real-time data.',
    images: ['/og-image.png'],
    creator: '@jrgoldmining',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    // Add Google Search Console verification here
    // google: 'your-google-verification-code',
  },
  alternates: {
    canonical: 'https://juniorgoldminingintelligence.com',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="32x32" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#D4AF37" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}
