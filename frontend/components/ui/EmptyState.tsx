"use client";

import Link from "next/link";

interface EmptyStateProps {
  /** What the user was looking for, e.g. "resource estimates". */
  title: string;
  /**
   * Why there is nothing here. Be specific about coverage — "only 7 of 396
   * companies have filed resource estimates" is useful; "no data" is not.
   */
  detail: string;
  /** Optional follow-on, e.g. a different tool that would work for them. */
  action?: { label: string; href: string };
}

/**
 * Explains an empty result instead of rendering blank.
 *
 * Several tools offer every company in a dropdown but can only answer for a
 * fraction of them — Resource Growth lists 396 and has data for 6 — so an
 * empty table reads as a broken tool rather than a coverage limit. Saying which
 * it is costs one line and prevents the support question.
 */
export default function EmptyState({ title, detail, action }: EmptyStateProps) {
  return (
    <div className="glass-card rounded-xl p-8 text-center">
      <div className="mx-auto mb-3 w-10 h-10 rounded-full border border-slate-700 flex items-center justify-center">
        <svg
          className="w-5 h-5 text-slate-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.8}
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <p className="text-slate-200 font-medium mb-1">{title}</p>
      <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
        {detail}
      </p>
      {action && (
        <Link
          href={action.href}
          className="inline-block mt-4 text-sm text-gold-400 hover:underline"
        >
          {action.label} →
        </Link>
      )}
    </div>
  );
}
