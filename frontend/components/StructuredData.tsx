'use client';

interface StructuredDataProps {
  data: Record<string, any>;
}

export default function StructuredData({ data }: StructuredDataProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

// Organization Schema for homepage
export function OrganizationSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Junior Gold Mining Intelligence',
    url: 'https://juniorminingintelligence.com',
    logo: {
      '@type': 'ImageObject',
      url: 'https://juniorminingintelligence.com/android-chrome-512x512.png',
      width: 512,
      height: 512,
    },
    description: 'AI-powered platform for analyzing and discovering junior gold mining companies with real-time data, resource estimates, and expert insights.',
    sameAs: [
      // Add social media profiles here
      // 'https://twitter.com/jrgoldmining',
      // 'https://linkedin.com/company/junior-gold-mining-intelligence',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'Customer Service',
      availableLanguage: 'English',
    },
  };

  return <StructuredData data={schema} />;
}

// Company/Corporation Schema
interface CompanySchemaProps {
  name: string;
  tickerSymbol: string;
  exchange: string;
  website?: string;
  headquarters?: string;
  description?: string;
}

export function CompanySchema({
  name,
  tickerSymbol,
  exchange,
  website,
  headquarters,
  description,
}: CompanySchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Corporation',
    name,
    tickerSymbol,
    description: description || `${name} is a junior gold mining and exploration company listed on ${exchange} under ticker ${tickerSymbol}.`,
    ...(website && { url: website }),
    ...(headquarters && {
      address: {
        '@type': 'PostalAddress',
        addressLocality: headquarters,
      },
    }),
    industry: 'Mining',
    sector: 'Precious Metals Exploration',
  };

  return <StructuredData data={schema} />;
}

// Mining Project Schema
interface ProjectSchemaProps {
  name: string;
  companyName: string;
  location?: string;
  commodity: string;
  description?: string;
}

export function MiningProjectSchema({
  name,
  companyName,
  location,
  commodity,
  description,
}: ProjectSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Place',
    name,
    description: description || `${name} is a ${commodity} exploration project operated by ${companyName}.`,
    ...(location && { address: location }),
    additionalType: 'Mining Project',
  };

  return <StructuredData data={schema} />;
}

// Article/NewsArticle Schema for news releases
interface NewsArticleSchemaProps {
  headline: string;
  datePublished: string;
  url: string;
  companyName: string;
  summary?: string;
}

export function NewsArticleSchema({
  headline,
  datePublished,
  url,
  companyName,
  summary,
}: NewsArticleSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline,
    datePublished,
    url,
    author: {
      '@type': 'Organization',
      name: companyName,
    },
    publisher: {
      '@type': 'Organization',
      name: 'Junior Gold Mining Intelligence',
      logo: {
        '@type': 'ImageObject',
        url: 'https://juniorminingintelligence.com/android-chrome-512x512.png',
        width: 512,
        height: 512,
      },
    },
    ...(summary && { description: summary }),
  };

  return <StructuredData data={schema} />;
}

// BreadcrumbList Schema for navigation
interface BreadcrumbItem {
  name: string;
  url: string;
}

interface BreadcrumbListSchemaProps {
  items: BreadcrumbItem[];
}

export function BreadcrumbListSchema({ items }: BreadcrumbListSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  };

  return <StructuredData data={schema} />;
}

// Dataset Schema for company data
interface DatasetSchemaProps {
  name: string;
  description: string;
  url: string;
}

export function DatasetSchema({ name, description, url }: DatasetSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name,
    description,
    url,
    creator: {
      '@type': 'Organization',
      name: 'Junior Gold Mining Intelligence',
    },
    keywords: ['gold mining', 'mineral exploration', 'mining data', 'resource estimates'],
  };

  return <StructuredData data={schema} />;
}
