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
  metadataBase: new URL('https://juniorminingintelligence.com'),
  title: {
    default: 'Junior Mining Stocks: Gold, Silver & Critical Minerals Intelligence 2026',
    template: '%s | Junior Mining Intelligence'
  },
  description: 'Track 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals. Real-time exploration data, NI 43-101 reports, TSXV listings, resource estimates. AI-powered mining intelligence platform.',
  keywords: [
    'junior mining',
    'gold mining stocks',
    'silver mining companies',
    'lithium exploration',
    'critical minerals',
    'rare earth elements',
    'copper mining',
    'nickel mining',
    'mining stocks',
    'mineral exploration',
    'TSXV mining',
    'TSX mining',
    'battery metals',
    'precious metals',
    'mining intelligence',
    'AI mining analysis',
    'exploration companies',
    'mineral resource estimates',
    'mining financings',
    'NI 43-101 reports'
  ],
  authors: [{ name: 'Junior Mining Intelligence' }],
  creator: 'Junior Mining Intelligence',
  publisher: 'Junior Mining Intelligence',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://juniorminingintelligence.com',
    siteName: 'Junior Mining Intelligence',
    title: 'Junior Mining Stocks: Gold, Silver & Critical Minerals Intelligence 2026',
    description: 'Track 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals. Real-time exploration data, NI 43-101 reports, TSXV listings.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Junior Mining Intelligence Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Junior Mining Stocks: Gold, Silver & Critical Minerals Intelligence 2026',
    description: 'Track 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths & critical minerals with AI-powered insights.',
    images: ['/og-image.png'],
    creator: '@jrminingintel',
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
    canonical: 'https://juniorminingintelligence.com',
  },
};

// JSON-LD structured data for rich snippets
const organizationJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  '@id': 'https://juniorminingintelligence.com/#organization',
  name: 'Junior Mining Intelligence',
  alternateName: 'JMI Platform',
  legalName: 'Junior Mining Intelligence',
  url: 'https://juniorminingintelligence.com',
  sameAs: [
    'https://www.wikidata.org/wiki/Q137719703',
    'https://www.linkedin.com/company/juniorminingintelligence',
    'https://twitter.com/JuniorMini82636',
    'https://www.facebook.com/profile.php?id=61586276247045'
  ],
  logo: {
    '@type': 'ImageObject',
    '@id': 'https://juniorminingintelligence.com/#logo',
    url: 'https://juniorminingintelligence.com/logo.png',
    contentUrl: 'https://juniorminingintelligence.com/logo.png',
    width: '512',
    height: '512',
    caption: 'Junior Mining Intelligence Logo'
  },
  image: {
    '@type': 'ImageObject',
    url: 'https://juniorminingintelligence.com/og-image.png',
    width: '1200',
    height: '630'
  },
  description: 'AI-powered platform for junior mining company analysis covering gold, silver, lithium, copper, rare earths, and critical minerals. Investment research and market intelligence for precious metals and battery metals.',
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
      '@id': 'https://www.wikidata.org/wiki/Q568',
      name: 'Lithium'
    },
    {
      '@type': 'Thing',
      '@id': 'https://www.wikidata.org/wiki/Q753',
      name: 'Copper'
    },
    {
      '@type': 'Thing',
      name: 'TSXV Mining Stocks'
    },
    {
      '@type': 'Thing',
      name: 'Critical Minerals Exploration'
    },
    {
      '@type': 'Thing',
      name: 'Rare Earth Elements'
    }
  ],
  mentions: {
    '@type': 'DefinedTerm',
    name: 'NI 43-101',
    inDefinedTermSet: 'Mining Industry Standards',
    description: 'Canadian National Instrument 43-101 standards for mineral resource reporting'
  },
  contactPoint: [
    {
      '@type': 'ContactPoint',
      contactType: 'customer service',
      availableLanguage: ['English'],
      email: 'info@juniorminingintelligence.com',
      contactOption: 'TollFree',
      areaServed: ['CA', 'US']
    },
    {
      '@type': 'ContactPoint',
      contactType: 'technical support',
      availableLanguage: ['English'],
      email: 'support@juniorminingintelligence.com',
      contactOption: 'TollFree',
      areaServed: ['CA', 'US']
    }
  ],
  address: {
    '@type': 'PostalAddress',
    addressCountry: 'CA',
    addressRegion: 'Canada'
  },
  foundingDate: '2024',
  slogan: 'AI-Powered Mining Intelligence Platform',
  knowsAbout: [
    'Junior Mining Companies',
    'Gold & Silver Exploration',
    'Critical Minerals',
    'Lithium & Battery Metals',
    'Rare Earth Elements',
    'NI 43-101 Technical Reports',
    'TSXV Stock Analysis',
    'Mining Investment Research',
    'Precious Metals Markets',
    'Mineral Resource Estimates',
    'Mining Financings',
    'Battery Metals Exploration',
    'Precious Metals Analysis'
  ],
  areaServed: [
    {
      '@type': 'Country',
      name: 'Canada',
      '@id': 'https://www.wikidata.org/wiki/Q16'
    },
    {
      '@type': 'Country',
      name: 'United States',
      '@id': 'https://www.wikidata.org/wiki/Q30'
    },
    {
      '@type': 'Country',
      name: 'Australia',
      '@id': 'https://www.wikidata.org/wiki/Q408'
    }
  ],
  hasOfferCatalog: {
    '@type': 'OfferCatalog',
    name: 'Mining Intelligence Services',
    itemListElement: [
      {
        '@type': 'Offer',
        itemOffered: {
          '@type': 'Service',
          name: 'Junior Mining Company Analysis',
          description: 'Comprehensive analysis of 500+ junior mining companies including gold, silver, lithium, copper, and critical minerals exploration'
        }
      },
      {
        '@type': 'Offer',
        itemOffered: {
          '@type': 'Service',
          name: 'NI 43-101 Report Database',
          description: 'Access to technical reports and mineral resource estimates'
        }
      },
      {
        '@type': 'Offer',
        itemOffered: {
          '@type': 'Service',
          name: 'Mining Market Intelligence',
          description: 'Real-time precious metals pricing, financing data, and exploration updates'
        }
      }
    ]
  }
};

const websiteJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'Junior Mining Intelligence',
  url: 'https://juniorminingintelligence.com',
  description: 'Discover and analyze junior mining companies exploring gold, silver, lithium, copper, and critical minerals with AI-powered insights.',
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: 'https://juniorminingintelligence.com/companies?search={search_term_string}'
    },
    'query-input': 'required name=search_term_string'
  }
};

const financeServiceJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FinancialService',
  name: 'Junior Mining Intelligence',
  url: 'https://juniorminingintelligence.com',
  description: 'Mining investment research platform providing company analysis for gold, silver, lithium, copper, rare earths, and critical minerals. Includes precious metals pricing and investment qualification services.',
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
      name: 'What is a junior mining company?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'A junior mining company is a small to mid-sized exploration or development company focused on discovering and developing mineral deposits including gold, silver, lithium, copper, rare earths, and other critical minerals. These companies typically have market capitalizations under $500 million and are listed on exchanges like the TSX Venture Exchange (TSXV) or TSX.'
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
      name: 'How do I track junior mining stocks?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Junior Mining Intelligence provides a comprehensive platform to track 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths, and critical minerals. Features include real-time exploration data, NI 43-101 technical reports, mineral resource estimates, project financings, and AI-powered analysis. Our database includes companies listed on TSXV, TSX, and other major exchanges.'
      }
    },
    {
      '@type': 'Question',
      name: 'What data does the platform provide?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Our platform provides comprehensive data including: company profiles and management teams, NI 43-101 technical reports, mineral resource estimates (gold, silver, copper, lithium, rare earths, nickel), exploration project details and locations, financing history and market data, news releases and press announcements, AI-powered company analysis, and real-time precious metals and critical minerals pricing.'
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
      item: 'https://juniorminingintelligence.com'
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Companies',
      item: 'https://juniorminingintelligence.com/companies'
    },
    {
      '@type': 'ListItem',
      position: 3,
      name: 'Properties',
      item: 'https://juniorminingintelligence.com/properties'
    },
    {
      '@type': 'ListItem',
      position: 4,
      name: 'Glossary',
      item: 'https://juniorminingintelligence.com/glossary'
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
