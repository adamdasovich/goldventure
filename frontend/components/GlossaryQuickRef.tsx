/**
 * GlossaryQuickRef - Quick reference widget linking to relevant glossary terms
 *
 * This component improves internal linking and helps users understand technical terms
 * while boosting SEO through strategic internal links to the glossary page.
 *
 * Usage on company pages, property pages, or anywhere mining terminology appears
 */

import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import GlossaryLink from './GlossaryLink';

interface QuickRefTerm {
  term: string;
  relevance?: string;
}

interface GlossaryQuickRefProps {
  /** Specific terms to highlight (optional - will show common terms if not provided) */
  terms?: QuickRefTerm[];
  /** Custom title for the widget */
  title?: string;
  /** Compact mode for sidebar display */
  compact?: boolean;
}

const DEFAULT_MINING_TERMS: QuickRefTerm[] = [
  { term: 'NI 43-101', relevance: 'Canadian technical reporting standard' },
  { term: 'Indicated Resource', relevance: 'Mid-level geological confidence' },
  { term: 'Inferred Resource', relevance: 'Preliminary resource estimate' },
  { term: 'Measured Resource', relevance: 'Highest geological confidence' },
  { term: 'Feasibility Study', relevance: 'Detailed economic analysis' },
  { term: 'PEA', relevance: 'Preliminary economics' },
  { term: 'TSXV', relevance: 'Canadian junior mining exchange' },
  { term: 'Junior Mining Company', relevance: 'Exploration-stage companies' },
];

export default function GlossaryQuickRef({
  terms = DEFAULT_MINING_TERMS,
  title = 'Mining Terminology Reference',
  compact = false,
}: GlossaryQuickRefProps) {
  if (compact) {
    return (
      <Card variant="glass-card" className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between mb-2">
            <CardTitle className="text-lg">{title}</CardTitle>
            <a
              href="/glossary"
              className="text-sm text-gold-400 hover:text-gold-300"
            >
              View All →
            </a>
          </div>
          <div className="flex flex-wrap gap-2">
            {terms.slice(0, 6).map((item, idx) => (
              <GlossaryLink
                key={idx}
                term={item.term}
                className="text-sm px-2 py-1 rounded bg-slate-700/30 hover:bg-slate-700/50 no-underline"
              />
            ))}
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card variant="glass-card" className="mb-8">
      <CardHeader>
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle className="text-xl mb-2">{title}</CardTitle>
            <CardDescription>
              Quick reference guide to common mining and investment terms
            </CardDescription>
          </div>
          <a
            href="/glossary"
            className="text-gold-400 hover:text-gold-300 flex items-center gap-2 whitespace-nowrap"
          >
            Full Glossary
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {terms.map((item, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
            >
              <svg
                className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div className="flex-1">
                <GlossaryLink term={item.term} className="font-medium" />
                {item.relevance && (
                  <p className="text-sm text-slate-400 mt-1">{item.relevance}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400">
            New to junior mining?{' '}
            <a href="/glossary" className="text-gold-400 hover:text-gold-300">
              Browse our complete glossary
            </a>
            {' '}of 60+ industry terms, or learn about{' '}
            <a href="/financial-hub" className="text-gold-400 hover:text-gold-300">
              mining investment fundamentals
            </a>.
          </p>
        </div>
      </CardHeader>
    </Card>
  );
}

/**
 * Context-specific term sets for different page types
 */

export const RESOURCE_TERMS: QuickRefTerm[] = [
  { term: 'Measured Resource', relevance: 'Highest confidence resource category' },
  { term: 'Indicated Resource', relevance: 'Moderate confidence resources' },
  { term: 'Inferred Resource', relevance: 'Preliminary resource estimates' },
  { term: 'Mineral Reserve', relevance: 'Economically mineable resources' },
  { term: 'NI 43-101', relevance: 'Canadian reporting standard' },
  { term: 'Grade', relevance: 'Metal concentration in ore' },
];

export const FINANCIAL_TERMS: QuickRefTerm[] = [
  { term: 'Private Placement', relevance: 'Direct equity financing method' },
  { term: 'Flow-Through Shares', relevance: 'Canadian tax-advantaged shares' },
  { term: 'Accredited Investor', relevance: 'Qualified investor status' },
  { term: 'NPV', relevance: 'Net present value of project' },
  { term: 'IRR', relevance: 'Internal rate of return' },
  { term: 'AISC', relevance: 'All-in sustaining costs' },
];

export const EXPLORATION_TERMS: QuickRefTerm[] = [
  { term: 'Drill Program', relevance: 'Systematic exploration drilling' },
  { term: 'Assay', relevance: 'Chemical analysis of samples' },
  { term: 'PEA', relevance: 'Preliminary economic assessment' },
  { term: 'Feasibility Study', relevance: 'Comprehensive project study' },
  { term: 'Qualified Person', relevance: 'NI 43-101 certified expert' },
  { term: 'Exploration Stage', relevance: 'Pre-production phase' },
];
