/**
 * GlossaryLink - Automatically links mining terminology to glossary page
 *
 * This component helps improve SEO through internal linking by automatically
 * detecting and linking key mining terms to their definitions in the glossary.
 *
 * Usage:
 * <GlossaryLink term="NI 43-101">NI 43-101 compliant report</GlossaryLink>
 * <GlossaryLink term="Indicated Resource" />
 */

interface GlossaryLinkProps {
  term: string;
  children?: React.ReactNode;
  className?: string;
}

export default function GlossaryLink({ term, children, className = '' }: GlossaryLinkProps) {
  // Convert term to URL-friendly anchor
  const anchor = term.toLowerCase().replace(/\s+/g, '-').replace(/[()]/g, '');

  // Get the first letter for the letter section
  const firstLetter = term[0].toUpperCase();

  return (
    <a
      href={`/glossary#letter-${firstLetter}`}
      className={`text-gold-400 hover:text-gold-300 underline decoration-dotted ${className}`}
      title={`View definition of ${term} in glossary`}
    >
      {children || term}
    </a>
  );
}

/**
 * Common mining terms that should be linked to glossary
 * Use this list to identify terms in content that should be auto-linked
 */
export const GLOSSARY_TERMS = [
  'NI 43-101',
  'Indicated Resource',
  'Inferred Resource',
  'Measured Resource',
  'TSXV',
  'TSX Venture Exchange',
  'Feasibility Study',
  'PEA',
  'Preliminary Economic Assessment',
  'Junior Mining',
  'Junior Mining Company',
  'Qualified Person',
  'Mineral Reserve',
  'Proven Reserve',
  'Probable Reserve',
  'Grade',
  'g/t',
  'Heap Leaching',
  'Open-Pit',
  'Underground Mining',
  'Flow-Through Shares',
  'Private Placement',
  'Accredited Investor',
  'All-in Sustaining Cost',
  'AISC',
  'NPV',
  'Net Present Value',
  'IRR',
  'Internal Rate of Return',
  'Drill Program',
  'Assay',
  'Orebody',
  'Ore Body',
  'Mineral Resource',
  'Exploration',
  'Development',
  'Production',
];

/**
 * Helper function to check if text contains glossary terms
 *
 * @param text - The text content to check
 * @returns Array of glossary terms found in the text
 *
 * Example:
 * const content = "This NI 43-101 compliant report shows Indicated Resources.";
 * const foundTerms = findGlossaryTerms(content);
 * // Returns: ['NI 43-101', 'Indicated Resources']
 */
export function findGlossaryTerms(text: string): string[] {
  if (!text) return [];

  const foundTerms: string[] = [];

  // Sort terms by length (descending) to match longer phrases first
  const sortedTerms = [...GLOSSARY_TERMS].sort((a, b) => b.length - a.length);

  for (const term of sortedTerms) {
    const regex = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
    if (regex.test(text)) {
      foundTerms.push(term);
    }
  }

  return foundTerms;
}
