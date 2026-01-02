import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Junior Gold Mining Glossary - NI 43-101, TSXV & Industry Terms',
  description: 'Comprehensive glossary of 60+ junior gold mining terms including NI 43-101 standards, TSXV definitions, resource classifications, exploration terminology, and mining investment concepts.',
  keywords: [
    'mining glossary',
    'NI 43-101',
    'TSXV definitions',
    'indicated resource',
    'inferred resource',
    'measured resource',
    'junior mining terms',
    'gold mining dictionary',
    'exploration glossary',
    'mining investment terms',
    'feasibility study definition',
    'PEA definition',
    'qualified person mining',
    'mineral reserve',
    'heap leaching',
    'grade g/t',
    'flow-through shares',
    'private placement',
    'accredited investor'
  ],
  openGraph: {
    title: 'Junior Gold Mining Glossary - Essential Industry Terms & Definitions',
    description: '60+ mining terms including NI 43-101 standards, TSXV definitions, resource classifications, and investment concepts.',
    type: 'website',
    url: 'https://juniorgoldminingintelligence.com/glossary',
  },
  alternates: {
    canonical: 'https://juniorgoldminingintelligence.com/glossary',
  },
};

export default function GlossaryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
