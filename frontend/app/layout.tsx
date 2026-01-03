import type { Metadata } from 'next';
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import ClientLayout from './ClientLayout';
import GoogleAnalytics from '@/components/GoogleAnalytics';

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
    default: 'Junior Gold Mining Stocks, Exploration Data & TSXV Intelligence 2026',
    template: '%s | Junior Gold Mining Intelligence'
  },
  description: 'Track 500+ junior gold mining stocks with real-time exploration data, NI 43-101 technical reports, TSXV listings, mineral resource estimates, and project financings. AI-powered junior mining intelligence platform for investors.',
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
    title: 'Junior Gold Mining Stocks, Exploration Data & TSXV Intelligence 2026',
    description: 'Track 500+ junior gold mining stocks with real-time exploration data, NI 43-101 technical reports, TSXV listings, and mineral resource estimates.',
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
    title: 'Junior Gold Mining Stocks, Exploration Data & TSXV Intelligence 2026',
    description: 'Track 500+ junior gold mining stocks with real-time exploration data, NI 43-101 technical reports, and TSXV listings.',
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
    google: 'Dl6Cet84N81hYfuQbcFr-CNUqfyv71gDQje7aOPqkqQ',
  },
  alternates: {
    canonical: 'https://juniorgoldminingintelligence.com',
  },
};

// JSON-LD structured data for rich snippets
const organizationJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'Junior Gold Mining Intelligence',
  url: 'https://juniorgoldminingintelligence.com',
  logo: 'https://juniorgoldminingintelligence.com/logo.png',
  description: 'AI-powered platform for junior gold mining company analysis, investment research, and precious metals market intelligence.',
  about: [
    {
      '@type': 'Thing',
      '@id': 'https://www.wikidata.org/wiki/Q44626',
      name: 'Junior Mining'
    },
    {
      '@type': 'Thing',
      '@id': 'https://www.wikidata.org/wiki/Q897308',
      name: 'Gold Mining'
    },
    {
      '@type': 'Thing',
      name: 'TSXV Mining Stocks'
    },
    {
      '@type': 'Thing',
      name: 'Gold Exploration Companies'
    }
  ],
  mentions: {
    '@type': 'DefinedTerm',
    name: 'NI 43-101',
    inDefinedTermSet: 'Mining Industry Standards',
    description: 'Canadian National Instrument 43-101 standards for mineral resource reporting'
  },
  sameAs: [
    'https://twitter.com/jrgoldmining',
    'https://www.linkedin.com/company/junior-gold-mining-intelligence',
    'https://www.facebook.com/juniorgoldmining'
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'customer service',
    availableLanguage: ['English'],
    email: 'info@juniorgoldminingintelligence.com'
  },
  foundingDate: '2024',
  slogan: 'AI-Powered Mining Intelligence Platform',
  knowsAbout: [
    'Junior Gold Mining',
    'Mineral Exploration',
    'NI 43-101 Technical Reports',
    'TSXV Stock Analysis',
    'Mining Investment Research',
    'Precious Metals Markets'
  ]
};

const websiteJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'Junior Gold Mining Intelligence',
  url: 'https://juniorgoldminingintelligence.com',
  description: 'Discover and analyze junior gold mining companies with AI-powered insights.',
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: 'https://juniorgoldminingintelligence.com/companies?search={search_term_string}'
    },
    'query-input': 'required name=search_term_string'
  }
};

const financeServiceJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FinancialService',
  name: 'Junior Gold Mining Intelligence',
  url: 'https://juniorgoldminingintelligence.com',
  description: 'Mining investment research platform providing company analysis, precious metals pricing, and investment qualification services.',
  address: {
    '@type': 'PostalAddress',
    addressCountry: 'CA'
  },
  areaServed: [
    {
      '@type': 'Country',
      name: 'Canada'
    },
    {
      '@type': 'Country',
      name: 'United States'
    }
  ],
  serviceType: ['Investment Research', 'Market Analysis', 'Investor Education']
};

const faqPageJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'What is a junior gold mining company?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'A junior gold mining company is a small to mid-sized exploration or development company focused on discovering and developing gold deposits. These companies typically have market capitalizations under $500 million and are listed on exchanges like the TSX Venture Exchange (TSXV) or TSX.'
      }
    },
    {
      '@type': 'Question',
      name: 'What is NI 43-101?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'NI 43-101 is a Canadian National Instrument that sets standards for disclosure of scientific and technical information about mineral projects. It requires all public disclosures of mineral resources and reserves to be prepared or supervised by a Qualified Person and to follow strict reporting standards.'
      }
    },
    {
      '@type': 'Question',
      name: 'How do I track junior gold mining stocks?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Junior Gold Mining Intelligence provides a comprehensive platform to track 500+ junior gold mining stocks with real-time exploration data, NI 43-101 technical reports, mineral resource estimates, project financings, and AI-powered analysis. Our database includes companies listed on TSXV, TSX, and other major exchanges.'
      }
    },
    {
      '@type': 'Question',
      name: 'What data does the platform provide?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Our platform provides comprehensive data including: company profiles and management teams, NI 43-101 technical reports, mineral resource estimates (gold, silver, copper), exploration project details and locations, financing history and market data, news releases and press announcements, AI-powered company analysis, and real-time precious metals pricing.'
      }
    },
    {
      '@type': 'Question',
      name: 'What are mineral resource categories?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Under NI 43-101, mineral resources are classified into three categories based on geological confidence: Inferred Resources (lowest confidence), Indicated Resources (moderate confidence), and Measured Resources (highest confidence). Measured and Indicated Resources can be converted to Mineral Reserves after economic feasibility is demonstrated.'
      }
    }
  ]
};

const breadcrumbJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Home',
      item: 'https://juniorgoldminingintelligence.com'
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Companies',
      item: 'https://juniorgoldminingintelligence.com/companies'
    },
    {
      '@type': 'ListItem',
      position: 3,
      name: 'Properties',
      item: 'https://juniorgoldminingintelligence.com/properties'
    },
    {
      '@type': 'ListItem',
      position: 4,
      name: 'Glossary',
      item: 'https://juniorgoldminingintelligence.com/glossary'
    }
  ]
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const gaId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

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
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(financeServiceJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqPageJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
        />
        {gaId && <GoogleAnalytics measurementId={gaId} />}
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
