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
 * Helper function to automatically wrap glossary terms in content
 *
 * @param text - The text content to process
 * @param maxLinks - Maximum number of terms to link (default: 5)
 * @returns JSX with glossary terms linked
 *
 * Example:
 * const content = "This NI 43-101 compliant report shows Indicated Resources of 1.5M oz at 2.5 g/t gold.";
 * const linkedContent = autoLinkGlossaryTerms(content);
 */
export function autoLinkGlossaryTerms(text: string, maxLinks: number = 5): React.ReactNode {
  if (!text) return text;

  let linkedCount = 0;
  const linkedTerms = new Set<string>();
  let result: React.ReactNode[] = [text];

  // Sort terms by length (descending) to match longer phrases first
  const sortedTerms = [...GLOSSARY_TERMS].sort((a, b) => b.length - a.length);

  for (const term of sortedTerms) {
    if (linkedCount >= maxLinks) break;
    if (linkedTerms.has(term.toLowerCase())) continue;

    // Create a case-insensitive regex to find the term
    const regex = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');

    // Process each element in result array
    result = result.flatMap((element) => {
      if (typeof element !== 'string') return [element];

      const matches = element.match(regex);
      if (!matches || matches.length === 0) return [element];

      // Only link the first occurrence
      const parts = element.split(regex);
      const match = matches[0];

      linkedCount++;
      linkedTerms.add(term.toLowerCase());

      return [
        parts[0],
        <GlossaryLink key={`${term}-${linkedCount}`} term={term}>
          {match}
        </GlossaryLink>,
        ...parts.slice(1).join(match),
      ].filter(Boolean);
    });
  }

  return result;
}
