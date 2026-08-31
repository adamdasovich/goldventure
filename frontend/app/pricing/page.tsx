"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  AVAILABLE_COUNT,
  FREE_TOOL_SLUGS,
  PROSPECTOR_COUNT,
} from "@/app/investor-tools/tools";
import {
  platformAPI,
  type PlatformTier,
  type PlatformSubscriptionStatus,
} from "@/lib/api";
import { SIGNUP_OFFER_FALLBACK, type SignupOffer } from "@/lib/signupOffer";
import { trackSubscribe } from "@/lib/analytics";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import SiteHeader from "@/components/SiteHeader";

// Used only if /platform/tiers/ is unreachable. The backend is the authority
// on price; these exist so the page still renders something sane offline.
const TIER_FALLBACK: Record<
  string,
  { monthly: string; annual: string; savings: string; trialDays: number }
> = {
  explorer: { monthly: "Free", annual: "Free", savings: "", trialDays: 0 },
  prospector: { monthly: "$10", annual: "$100", savings: "$20", trialDays: 7 },
  miner: { monthly: "$50", annual: "$500", savings: "$100", trialDays: 7 },
};

// Only differences the backend actually enforces belong in this table. It
// previously advertised CSV export, an API, email alerts and priority chat -
// none of which exist.
//
// Miner is deliberately thin right now. The early-access welcome email of
// 2026-08-04 told recipients Prospector included unlimited chat and all the
// tools that existed then, so those cannot be moved behind Miner without
// breaking that promise. Only tools introduced after that date are eligible;
// Warrant Overhang Radar (2026-08-11) is the first.
const FEATURE_ROWS = [
  {
    label: "AI Chat (Claude)",
    explorer: "5 messages/day",
    prospector: "Unlimited",
    miner: "Unlimited",
  },
  {
    // Derived from the tool catalogue, not hand-counted. These said
    // "2 / 16 / All 17" while 19 tools were live — the same drift that put
    // stale counts in the sitemap.
    label: "Investor Tools",
    explorer: `${FREE_TOOL_SLUGS.length} tools`,
    prospector: `${PROSPECTOR_COUNT} tools`,
    miner: `All ${AVAILABLE_COUNT} tools`,
  },
  {
    label: "Warrant Overhang Radar",
    explorer: false,
    prospector: false,
    miner: true,
  },
  {
    label: "Open Financings",
    explorer: "5 latest only",
    prospector: "All open rounds",
    miner: "All open rounds",
  },
  {
    // requires_tier('prospector') on register_investment_interest. Explorers
    // can see the rounds they are allowed to see; acting on one is paid.
    label: "Participate in Financings",
    explorer: false,
    prospector: true,
    miner: true,
  },
  {
    // tier_gated(stub=('companies',)) on daily_briefing. Explorers keep the
    // headline and stats and lose the per-company detail, so this is a
    // truncation rather than a lock.
    label: "Daily Briefing",
    explorer: "Headline only",
    prospector: "Full detail",
    miner: "Full detail",
  },
  {
    // Re-added 2026-08-26. The note above is right that this was advertised
    // once without existing; export_companies_csv now does, behind
    // requires_tier('prospector'). Do not list a feature here before the
    // endpoint that backs it is live.
    label: "Database CSV Export",
    explorer: false,
    prospector: true,
    miner: true,
  },
  {
    // Any authenticated user can join — ForumConsumer only checks
    // is_authenticated, with no tier check — so Explorer gets a tick.
    label: "Company Discussion Boards",
    explorer: true,
    prospector: true,
    miner: true,
  },
  { label: "Company Directory", explorer: true, prospector: true, miner: true },
  { label: "News Feed", explorer: true, prospector: true, miner: true },
  { label: "Metals Pricing", explorer: true, prospector: true, miner: true },
  {
    label: "Prospector's Exchange",
    explorer: true,
    prospector: true,
    miner: true,
  },
];

function formatDay(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { month: "long", day: "numeric" });
}

export default function PricingPage() {
  const { user, accessToken, subscription } = useAuth();
  const [interval, setInterval] = useState<"month" | "year">("year");
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState("");
  const conversionFired = useRef(false);

  // Live pricing from the backend, so the page can't drift from what Stripe
  // actually charges. TIER_FALLBACK covers the request failing.
  const [tiers, setTiers] = useState<PlatformTier[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    platformAPI
      .getTiers()
      .then((res) => {
        if (!cancelled) setTiers(res.tiers);
      })
      .catch(() => {
        /* keep the fallback prices */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // What a brand-new registration grants today. Read, never hardcoded: the
  // grant is behind WELCOME_FREE_MONTH_ENABLED on the server, so writing "30
  // days free" into this page would turn it into a lie the moment that env var
  // is flipped. The fallback assumes the promo is OFF.
  const [offer, setOffer] = useState<SignupOffer>(SIGNUP_OFFER_FALLBACK);
  useEffect(() => {
    let cancelled = false;
    platformAPI
      .getSignupOffer()
      .then((res) => {
        if (!cancelled) setOffer(res);
      })
      .catch(() => {
        /* keep the conservative fallback */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Trial eligibility and whether there is a Stripe customer behind this user.
  // /auth/me carries neither, and both change what the buttons should say.
  const [status, setStatus] = useState<PlatformSubscriptionStatus | null>(null);
  useEffect(() => {
    if (!accessToken) {
      setStatus(null);
      return;
    }
    let cancelled = false;
    platformAPI
      .getSubscription(accessToken)
      .then((res) => {
        if (!cancelled) setStatus(res);
      })
      .catch(() => {
        /* fall back to the optimistic defaults below */
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const priceOf = (id: string) => {
    const t = tiers?.find((x) => x.id === id);
    if (!t) return TIER_FALLBACK[id];
    return {
      monthly: t.monthly_price,
      annual: t.annual_price,
      savings: t.annual_savings ?? "",
      trialDays: t.trial_days,
    };
  };

  useEffect(() => {
    // Read the query string off `window` rather than `useSearchParams()` — the
    // hook opts this statically-rendered page out of prerendering, and the
    // Suspense boundary it forced had no fallback, so the whole pricing page
    // was served to crawlers as an empty <body>. This effect is client-only
    // anyway, so nothing is lost.
    const query = new URLSearchParams(window.location.search);
    if (query.get("success") !== "true") return;

    // Google Ads / GA4 conversion: paid subscription completed. Ref-guarded
    // so a re-render can't double-count the conversion.
    if (!conversionFired.current) {
      conversionFired.current = true;
      trackSubscribe();
    }

    // The webhook is asynchronous, so the tier on /auth/me may still say
    // Explorer at this point. Reconcile against the session id Stripe put in
    // the URL rather than claiming success and showing the old tier.
    const sessionId = query.get("session_id");
    if (sessionId && accessToken) {
      setSuccessMessage("Confirming your subscription…");
      platformAPI
        .confirmCheckout(accessToken, sessionId)
        .then((res) => {
          setSuccessMessage(
            res.status === "active"
              ? "Your subscription is now active! Welcome aboard."
              : "Payment received — your subscription will activate shortly.",
          );
        })
        .catch(() => {
          setSuccessMessage(
            "Payment received — your subscription will activate shortly.",
          );
        });
    } else {
      setSuccessMessage("Your subscription is now active! Welcome aboard.");
    }

    const t = setTimeout(() => setSuccessMessage(""), 8000);
    return () => clearTimeout(t);
  }, [accessToken]);

  const handleSubscribe = async (tier: string) => {
    if (!accessToken) {
      // Redirect to login - they can come back
      window.location.href = "/?login=true";
      return;
    }

    setLoadingTier(tier);
    try {
      const baseUrl = window.location.origin;
      const res = await platformAPI.createCheckout(
        accessToken,
        tier,
        interval,
        baseUrl,
      );
      window.location.href = res.checkout_url;
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to start checkout");
      setLoadingTier(null);
    }
  };

  const handleManageBilling = async () => {
    if (!accessToken) return;
    try {
      const res = await platformAPI.getBillingPortal(
        accessToken,
        window.location.href,
      );
      window.location.href = res.portal_url;
    } catch (err) {
      alert(
        err instanceof Error ? err.message : "Failed to open billing portal",
      );
    }
  };

  const currentTier = subscription?.effective_tier || "explorer";
  const trialDays = priceOf("prospector").trialDays;

  // One trial per customer: has_used_trial() means a returning subscriber pays
  // from day one. Promising them a free week on the button and then charging
  // at checkout is the kind of thing that produces a chargeback, so the label
  // asks. Optimistic until the status arrives, matching the backend default.
  const trialEligible = status ? status.trial_eligible : true;

  // A comp grant (early-access gift) reads as an active paid tier but carries
  // no Stripe customer, so there is no billing portal behind it. Offering one
  // to those users produced "No billing account found." and nothing else.
  const hasBilling = !!status?.has_billing_account;
  const compEndsOn =
    currentTier !== "explorer" && status && !hasBilling
      ? (status.trial_end ?? status.current_period_end ?? null)
      : null;

  const ctaLabel =
    trialEligible && trialDays > 0
      ? `Start ${trialDays}-Day Free Trial`
      : "Subscribe";

  /** The button under a paid plan, plus the line explaining a comp grant. */
  const planCta = (tier: "prospector" | "miner", primary: boolean) => {
    const onThisPlan = currentTier === tier;

    if (onThisPlan && hasBilling) {
      return (
        <Button
          variant="secondary"
          size="lg"
          className="w-full"
          onClick={handleManageBilling}
        >
          Manage Subscription
        </Button>
      );
    }

    return (
      <>
        <Button
          variant={primary ? "primary" : "secondary"}
          size="lg"
          className={primary ? "w-full cta-glow" : "w-full"}
          onClick={() => handleSubscribe(tier)}
          disabled={loadingTier === tier}
        >
          {loadingTier === tier ? "Redirecting..." : ctaLabel}
        </Button>
        {onThisPlan && compEndsOn && (
          <p className="mt-2 text-center text-xs text-slate-400">
            Your free access runs to {formatDay(compEndsOn)}. Subscribe to keep
            it after that.
          </p>
        )}
      </>
    );
  };

  const renderCellValue = (value: string | boolean) => {
    if (value === true)
      return <span className="text-emerald-400">&#10003;</span>;
    if (value === false) return <span className="text-slate-600">&mdash;</span>;
    return <span className="text-slate-300 text-sm">{value}</span>;
  };

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <SiteHeader />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Success banner */}
        {successMessage && (
          <div className="mb-8 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
            <p className="text-emerald-400 font-medium">{successMessage}</p>
          </div>
        )}

        {/* Header */}
        <div className="text-center mb-12">
          <Badge variant="gold" className="mb-4">
            Choose Your Plan
          </Badge>
          <h1 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gold-400 mb-4 tracking-tight italic">
            Mining Intelligence, Your Way
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Start free with Explorer. Upgrade when you need unlimited AI chat,{" "}
            {PROSPECTOR_COUNT} investor tools, every open financing round — and
            the ability to participate in one.
          </p>
        </div>

        {/* The signup grant is a better offer than anything on this page, and
            it was the one thing /pricing never mentioned. Only shown to
            logged-out visitors — anyone signed in already has it or has had
            it — and only while the server says it is switched on. */}
        {!user && offer.free_trial_enabled && (
          <div className="mb-12 rounded-xl border border-gold-500/30 bg-slate-900/60 px-6 py-4 text-center">
            <p className="text-slate-300">
              <span className="font-semibold text-gold-400">
                New accounts get {offer.free_trial_days} days of Prospector
                free.
              </span>{" "}
              No credit card, nothing to cancel — it reverts to Explorer on its
              own.
            </p>
          </div>
        )}

        {/* Interval Toggle */}
        <div className="flex items-center justify-center gap-3 mb-12">
          <button
            onClick={() => setInterval("month")}
            className={`px-4 py-2 min-h-11 lg:min-h-0 inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all ${
              interval === "month"
                ? "bg-gold-500/20 text-gold-400 border border-gold-500/30"
                : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setInterval("year")}
            className={`px-4 py-2 min-h-11 lg:min-h-0 inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all ${
              interval === "year"
                ? "bg-gold-500/20 text-gold-400 border border-gold-500/30"
                : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Annual
            <span className="ml-2 text-xs text-emerald-400">Save 2 months</span>
          </button>
        </div>

        {/* Currency note */}
        <p className="text-center text-sm text-slate-400 -mt-8 mb-12">
          All prices in Canadian dollars (CAD)
        </p>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {/* Explorer - free forever */}
          <div
            className={`glass-card rounded-2xl p-6 flex flex-col ${currentTier === "explorer" ? "border-gold-500/40" : ""}`}
          >
            <div className="mb-6">
              <h3 className="text-xl font-bold text-slate-200">Explorer</h3>
              <p className="text-sm text-slate-400 mt-1">
                Get started for free
              </p>
              <div className="mt-4">
                <span className="text-4xl font-bold text-white">$0</span>
                <span className="text-slate-400 ml-1">/forever</span>
              </div>
            </div>
            <ul className="space-y-3 mb-8 flex-1">
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-emerald-400 mt-0.5">&#10003;</span>
                Browse 390+ company profiles
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-emerald-400 mt-0.5">&#10003;</span>5 AI
                chat messages per day
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-emerald-400 mt-0.5">&#10003;</span>
                Grade Ranker &amp; Sector Pulse tools
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-emerald-400 mt-0.5">&#10003;</span>
                Daily mining news feed
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-emerald-400 mt-0.5">&#10003;</span>
                Current metals pricing
              </li>
            </ul>
            {currentTier === "explorer" ? (
              <Button variant="ghost" size="lg" className="w-full" disabled>
                Current Plan
              </Button>
            ) : (
              <Button variant="ghost" size="lg" className="w-full" disabled>
                Free Tier
              </Button>
            )}
          </div>

          {/* Prospector - price comes from /platform/tiers/, never from here */}
          <div
            className={`glass-card rounded-2xl p-6 flex flex-col relative border-gold-500/30 ${currentTier === "prospector" ? "border-gold-400/60" : ""}`}
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <Badge variant="gold">Most Popular</Badge>
            </div>
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gold-400">Prospector</h3>
              <p className="text-sm text-slate-400 mt-1">
                For serious investors
              </p>
              <div className="mt-4">
                <span className="text-4xl font-bold text-white">
                  {interval === "month"
                    ? priceOf("prospector").monthly
                    : priceOf("prospector").annual}
                </span>
                <span className="text-slate-400 ml-1">
                  /{interval === "month" ? "month" : "year"}
                </span>
                {interval === "year" && (
                  <span className="block text-xs text-emerald-400 mt-1">
                    Save {priceOf("prospector").savings}/year vs monthly
                  </span>
                )}
              </div>
            </div>
            {/* Every line here is something the backend enforces. "Full company
                profiles + resources" used to sit in this list and nothing gated
                it — Explorer sees the same profiles. */}
            <ul className="space-y-3 mb-8 flex-1">
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                <strong className="text-white">Unlimited</strong>&nbsp;AI chat
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                <strong className="text-white">{PROSPECTOR_COUNT}</strong>
                &nbsp;investor tools
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Every open financing round, and the ability to participate
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                The full company database as a CSV export
              </li>
            </ul>
            {planCta("prospector", true)}
          </div>

          {/* Miner - price comes from /platform/tiers/, never from here */}
          <div
            className={`glass-card rounded-2xl p-6 flex flex-col ${currentTier === "miner" ? "border-gold-500/40" : ""}`}
          >
            <div className="mb-6">
              <h3 className="text-xl font-bold text-slate-200">Miner</h3>
              <p className="text-sm text-slate-400 mt-1">
                Maximum power for professionals
              </p>
              <div className="mt-4">
                <span className="text-4xl font-bold text-white">
                  {interval === "month"
                    ? priceOf("miner").monthly
                    : priceOf("miner").annual}
                </span>
                <span className="text-slate-400 ml-1">
                  /{interval === "month" ? "month" : "year"}
                </span>
                {interval === "year" && (
                  <span className="block text-xs text-emerald-400 mt-1">
                    Save {priceOf("miner").savings}/year vs monthly
                  </span>
                )}
              </div>
            </div>
            <ul className="space-y-3 mb-8 flex-1">
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Everything in Prospector, plus:
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Warrant Overhang Radar
              </li>
            </ul>
            {planCta("miner", false)}
          </div>
        </div>

        {/* Feature Comparison Table */}
        <div className="mb-16">
          <h2 className="font-display text-2xl font-semibold text-gold-400 text-center mb-8 tracking-tight italic">
            Full Feature Comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">
                    Feature
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-400">
                    Explorer
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gold-400">
                    Prospector
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-slate-400">
                    Miner
                  </th>
                </tr>
              </thead>
              <tbody>
                {FEATURE_ROWS.map((row, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="py-3 px-4 text-sm text-slate-300">
                      {row.label}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {renderCellValue(row.explorer)}
                    </td>
                    <td className="py-3 px-4 text-center bg-gold-500/5">
                      {renderCellValue(row.prospector)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {renderCellValue(row.miner)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ. The trial answer is assembled from the same two sources the
            buttons use, because there are two different free periods here and
            conflating them is how "you'll be charged automatically" ended up
            attached to a 30-day grant that takes no card. */}
        <div className="max-w-3xl mx-auto">
          <h2 className="font-display text-2xl font-semibold text-gold-400 text-center mb-8 tracking-tight italic">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {[
              {
                q: "Can I cancel anytime?",
                a: "Yes. Cancel anytime from your billing portal. You'll keep access until the end of the period you've paid for.",
              },
              {
                q: "What free access is there?",
                a: offer.free_trial_enabled
                  ? `Two separate things. Creating an account gives you ${offer.free_trial_days} days of Prospector with no card — when it runs out you drop to Explorer and nothing is charged. Separately, the first time you start a paid plan it includes a ${trialDays}-day trial.`
                  : `Explorer is free forever. The first time you start a paid plan it includes a ${trialDays}-day trial.`,
              },
              {
                q: "What happens when the paid trial ends?",
                a: `You're charged automatically at the end of the ${trialDays} days unless you cancel first. The trial is once per customer — if you've subscribed before, a new plan starts billing immediately.`,
              },
              {
                q: "Can I switch between plans?",
                a: "Yes. Change plans from the billing portal once you're subscribed.",
              },
              {
                q: "Is my payment secure?",
                a: "All payments are processed by Stripe, the same payment infrastructure used by Amazon, Google, and thousands of public companies.",
              },
            ].map((faq, i) => (
              <div key={i} className="glass-card rounded-xl p-5">
                <h3 className="font-medium text-white mb-2">{faq.q}</h3>
                <p className="text-sm text-slate-400">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
