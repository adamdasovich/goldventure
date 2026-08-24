"use client";

import { Button } from "@/components/ui/Button";

/**
 * Free-account conversion prompt.
 *
 * Exists because /companies took 53 of 64 paid-search sessions in the week to
 * 2026-08-24 — people arriving from ads, reading for 7-8 minutes, and leaving.
 * The page had no signup CTA at all: zero occurrences of "sign up", "get
 * started", "create account", or any link to registration. ~CA$106 of ad spend
 * produced zero `sign_up` events, not because the traffic was poor (50-88%
 * engagement, sessions over 460s) but because nothing ever asked.
 *
 * `onRegister` should open the existing RegisterModal. The `sign_up` GA4/Ads
 * conversion fires on its own — AuthContext sets a sessionStorage flag during
 * register() and dispatches on the following page load — so there is nothing
 * to instrument here.
 *
 * Only render this for logged-out visitors; the caller owns that check.
 *
 * Claims below are limited to what the Explorer (free) tier actually includes
 * per the pricing table: company directory, news feed, metals pricing, 5 AI
 * chat messages/day, and the 5 latest open financings. Don't add benefits here
 * without checking app/pricing/page.tsx first — an over-promise costs more
 * than the signup is worth.
 */

interface FreeAccountCTAProps {
  onRegister: () => void;
  onSignIn?: () => void;
  /** "banner" is compact, for above the fold. "panel" is fuller, for below content. */
  variant?: "banner" | "panel";
  className?: string;
}

const BENEFITS = [
  "Ask the AI 5 research questions a day",
  "See the latest open financing rounds",
  "Daily metals pricing and company news",
];

export function FreeAccountCTA({
  onRegister,
  onSignIn,
  variant = "panel",
  className = "",
}: FreeAccountCTAProps) {
  if (variant === "banner") {
    return (
      <div
        className={`flex flex-col sm:flex-row items-center justify-center gap-4 rounded-xl border border-gold-500/30 bg-slate-900/60 px-6 py-4 ${className}`}
      >
        <p className="text-slate-300 text-center sm:text-left">
          <span className="text-white font-semibold">Researching a company?</span>{" "}
          Create a free account to ask the AI about it — no credit card.
        </p>
        <Button variant="primary" onClick={onRegister} className="shrink-0">
          Create free account
        </Button>
      </div>
    );
  }

  return (
    <div
      className={`rounded-2xl border border-gold-500/30 bg-linear-to-b from-slate-900 to-slate-800/60 px-6 py-10 sm:px-10 text-center ${className}`}
    >
      <h2 className="text-2xl sm:text-3xl font-bold text-gradient-gold mb-3 leading-tight pb-1">
        Go deeper on any of these companies
      </h2>
      <p className="text-slate-300 max-w-2xl mx-auto mb-6">
        A free account unlocks the research tools behind this directory. No
        credit card, no trial to cancel.
      </p>

      <ul className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-6 mb-8 text-sm text-slate-300">
        {BENEFITS.map((benefit) => (
          <li key={benefit} className="flex items-center justify-center gap-2">
            <svg
              className="w-4 h-4 text-gold-400 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            {benefit}
          </li>
        ))}
      </ul>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Button variant="primary" size="lg" onClick={onRegister}>
          Create free account
        </Button>
        {onSignIn && (
          <button
            type="button"
            onClick={onSignIn}
            className="text-sm text-slate-400 hover:text-gold-300 transition-colors px-3 py-2 min-h-11"
          >
            Already have an account? Sign in
          </button>
        )}
      </div>
    </div>
  );
}

export default FreeAccountCTA;
