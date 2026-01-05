import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Junior Mining Glossary - Gold, Silver, Lithium, REE & Critical Minerals Terms',
  description: 'Comprehensive glossary of 100+ mining terms including gold, silver, lithium, rare earths, battery metals, critical minerals, NI 43-101 standards, TSXV definitions, resource classifications, and investment concepts.',
  keywords: [
    'mining glossary',
    'NI 43-101',
    'TSXV definitions',
    'indicated resource',
    'inferred resource',
    'measured resource',
    'junior mining terms',
    'mining dictionary',
    'exploration glossary',
    'lithium glossary',
    'rare earth terms',
    'battery metals glossary',
    'critical minerals definitions',
    'silver mining terms',
    'copper mining glossary',
    'feasibility study definition',
    'PEA definition',
    'qualified person mining',
    'mineral reserve',
    'NMC battery',
    'LFP battery',
    'REE TREO',
    'spodumene lithium',
    'cobalt sulphate',
    'nickel sulphate',
    'graphite anode'
  ],
  openGraph: {
    title: 'Junior Mining Glossary - Gold, Silver, Lithium, REE & Critical Minerals',
    description: '100+ mining terms covering gold, silver, lithium, rare earths, battery metals, critical minerals, NI 43-101 standards, and investment concepts.',
    type: 'website',
    url: 'https://juniorminingintelligence.com/glossary',
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/glossary',
  },
};

export default function GlossaryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
