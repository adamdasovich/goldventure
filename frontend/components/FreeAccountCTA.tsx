"use client";

import { Button } from "@/components/ui/Button";
import {
  type SignupOffer,
  SIGNUP_OFFER_FALLBACK,
} from "@/lib/signupOffer";

/**
 * Free-account conversion prompt.
 *
 * Exists because /companies took 53 of 64 paid-search sessions in the week to
 * 2026-08-24 and had no way to register. Scanned logged-out, the page contained
 * zero occurrences of "sign up", "get started" or "create account". ~CA$106 of
 * ad spend produced zero sign_up events — not because the traffic was poor
 * (50-88% engagement, sessions over 460s) but because nothing ever asked.
 *
 * The copy is driven by `offer`, fetched from /api/platform/signup-offer/,
 * NOT hardcoded. Registration grants a 30-day comp Prospector subscription via
 * deliver_welcome() -> grant_free_month(), but only while the server's
 * WELCOME_FREE_MONTH_ENABLED is on. Hardcoding "free month" would mean flipping
 * that env var silently turns this page into a lie. When the offer is off (or
 * unreachable) this falls back to describing the Explorer tier, which is always
 * true.
 *
 * `onRegister` should open the existing RegisterModal. The `sign_up` GA4/Ads
 * conversion fires on its own — AuthContext defers it to the page load after
 * register() — so there is nothing to instrument here.
 *
 * Only render for logged-out visitors; the caller owns that check.
 */

interface FreeAccountCTAProps {
  onRegister: () => void;
  onSignIn?: () => void;
  /** From fetchSignupOffer(). Omitted = assume the promo is off. */
  offer?: SignupOffer;
  /** "banner" is compact, for above the fold. "panel" is fuller, for below content. */
  variant?: "banner" | "panel";
  className?: string;
}

function copyFor(offer: SignupOffer) {
  if (offer.free_trial_enabled) {
    const chat = offer.free_trial_unlimited_chat
      ? "Unlimited AI research on any company"
      : "AI research on any company";
    return {
      bannerLead: "Researching a company?",
      bannerBody: `Get ${offer.free_trial_days} days of full access free — no credit card.`,
      heading: `Go deeper — ${offer.free_trial_days} days free`,
      sub: `Creating an account starts a ${offer.free_trial_days}-day Prospector trial. No credit card, nothing to cancel — it reverts to the free plan on its own.`,
      benefits: [
        chat,
        // Free accounts see 5 of the live rounds; the trial opens all of them
        // and the flow to act on one. Verified in open_financings.py and
        // requires_tier on register_investment_interest.
        "Every open financing round, and the ability to participate",
        "All 19 investor tools, and the database as CSV",
        // Capability, not activity: 389 of 396 discussions had no messages as
        // of 2026-08-26, so "see what investors are saying" would be a promise
        // most company pages cannot keep.
        "A live discussion board on every company",
      ],
      cta: "Start free trial",
    };
  }
  return {
    bannerLead: "Researching a company?",
    bannerBody: "Create a free account to ask the AI about it — no credit card.",
    heading: "Go deeper on any of these companies",
    sub: "A free account unlocks the research tools behind this directory. No credit card, no trial to cancel.",
    benefits: [
      `Ask the AI ${offer.fallback_chat_limit} research questions a day`,
      "A live discussion board on every company",
      "Daily metals pricing and company news",
    ],
    cta: "Create free account",
  };
}

export function FreeAccountCTA({
  onRegister,
  onSignIn,
  offer = SIGNUP_OFFER_FALLBACK,
  variant = "panel",
  className = "",
}: FreeAccountCTAProps) {
  const copy = copyFor(offer);

  if (variant === "banner") {
    return (
      <div
        className={`flex flex-col sm:flex-row items-center justify-center gap-4 rounded-xl border border-gold-500/30 bg-slate-900/60 px-6 py-4 ${className}`}
      >
        <p className="text-slate-300 text-center sm:text-left">
          <span className="text-white font-semibold">{copy.bannerLead}</span>{" "}
          {copy.bannerBody}
        </p>
        <Button variant="primary" onClick={onRegister} className="shrink-0">
          {copy.cta}
        </Button>
      </div>
    );
  }

  return (
    <div
      className={`rounded-2xl border border-gold-500/30 bg-linear-to-b from-slate-900 to-slate-800/60 px-6 py-10 sm:px-10 text-center ${className}`}
    >
      <h2 className="font-display text-2xl sm:text-3xl font-semibold text-gold-400 mb-3 leading-tight tracking-tight italic">
        {copy.heading}
      </h2>
      <p className="text-slate-300 max-w-2xl mx-auto mb-6">{copy.sub}</p>

      <ul className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-6 mb-8 text-sm text-slate-300">
        {copy.benefits.map((benefit) => (
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
          {copy.cta}
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
