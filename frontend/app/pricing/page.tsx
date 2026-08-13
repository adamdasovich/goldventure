"use client";

import { Suspense, useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { platformAPI } from "@/lib/api";
import { trackSubscribe } from "@/lib/analytics";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import LogoMono from "@/components/LogoMono";

// Only differences the backend actually enforces belong in this table. It
// previously advertised CSV export, an API, email alerts and priority chat -
// none of which exist - and claimed both paid tiers had unlimited chat and the
// same tools, which made Miner a 3.3x price for an identical product.
const FEATURE_ROWS = [
  {
    label: "AI Chat (Claude)",
    explorer: "5 messages/day",
    prospector: "100 messages/day",
    miner: "Unlimited",
  },
  {
    label: "Investor Tools",
    explorer: "2 tools",
    prospector: "13 tools",
    miner: "All 17 tools",
  },
  {
    label: "Warrant Overhang Radar",
    explorer: false,
    prospector: false,
    miner: true,
  },
  {
    label: "Property Valuation",
    explorer: false,
    prospector: false,
    miner: true,
  },
  {
    label: "Due-Diligence Assistant",
    explorer: false,
    prospector: false,
    miner: true,
  },
  { label: "Portfolio X-Ray", explorer: false, prospector: false, miner: true },
  {
    label: "Open Financings",
    explorer: "5 latest only",
    prospector: "All open rounds",
    miner: "All open rounds",
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

export default function PricingPage() {
  return (
    <Suspense>
      <PricingContent />
    </Suspense>
  );
}

function PricingContent() {
  const { user, accessToken, subscription } = useAuth();
  const searchParams = useSearchParams();
  const [interval, setInterval] = useState<"month" | "year">("year");
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState("");
  const conversionFired = useRef(false);

  useEffect(() => {
    if (searchParams.get("success") === "true") {
      setSuccessMessage("Your subscription is now active! Welcome aboard.");
      // Google Ads / GA4 conversion: paid subscription completed. Ref-guarded
      // so a re-render can't double-count the conversion.
      if (!conversionFired.current) {
        conversionFired.current = true;
        trackSubscribe();
      }
      // Clear after 8 seconds
      const t = setTimeout(() => setSuccessMessage(""), 8000);
      return () => clearTimeout(t);
    }
  }, [searchParams]);

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

  const renderCellValue = (value: string | boolean) => {
    if (value === true)
      return <span className="text-emerald-400">&#10003;</span>;
    if (value === false) return <span className="text-slate-600">&mdash;</span>;
    return <span className="text-slate-300 text-sm">{value}</span>;
  };

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-3">
              <LogoMono className="h-10" />
            </Link>
            <Link href="/">
              <Button variant="ghost" size="sm">
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </nav>

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
          <h1 className="text-4xl sm:text-5xl font-bold text-gradient-gold mb-4">
            Mining Intelligence, Your Way
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Start free with Explorer. Upgrade when you need unlimited AI chat,
            more investor tools, and every open financing round.
          </p>
        </div>

        {/* Interval Toggle */}
        <div className="flex items-center justify-center gap-3 mb-12">
          <button
            onClick={() => setInterval("month")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              interval === "month"
                ? "bg-gold-500/20 text-gold-400 border border-gold-500/30"
                : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setInterval("year")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
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
          {/* Explorer - Free */}
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
                Browse 500+ company profiles
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

          {/* Prospector - $29/mo */}
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
                  {interval === "month" ? "$15" : "$150"}
                </span>
                <span className="text-slate-400 ml-1">
                  /{interval === "month" ? "month" : "year"}
                </span>
                {interval === "year" && (
                  <span className="block text-xs text-emerald-400 mt-1">
                    Save $30/year vs monthly
                  </span>
                )}
              </div>
            </div>
            <ul className="space-y-3 mb-8 flex-1">
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                <strong className="text-white">100</strong>&nbsp;AI chat messages/day
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                <strong className="text-white">13</strong>&nbsp;investor tools
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Every open financing round
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Full company profiles + resources
              </li>
            </ul>
            {currentTier === "prospector" ? (
              <Button
                variant="secondary"
                size="lg"
                className="w-full"
                onClick={handleManageBilling}
              >
                Manage Subscription
              </Button>
            ) : (
              <Button
                variant="primary"
                size="lg"
                className="w-full cta-glow"
                onClick={() => handleSubscribe("prospector")}
                disabled={loadingTier === "prospector"}
              >
                {loadingTier === "prospector"
                  ? "Redirecting..."
                  : "Start 7-Day Free Trial"}
              </Button>
            )}
          </div>

          {/* Miner - $79/mo */}
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
                  {interval === "month" ? "$50" : "$500"}
                </span>
                <span className="text-slate-400 ml-1">
                  /{interval === "month" ? "month" : "year"}
                </span>
                {interval === "year" && (
                  <span className="block text-xs text-emerald-400 mt-1">
                    Save $100/year vs monthly
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
                <strong className="text-white">Unlimited</strong>&nbsp;AI chat
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Warrant Overhang Radar
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Property Valuation
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Due-Diligence Assistant
              </li>
              <li className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-gold-400 mt-0.5">&#10003;</span>
                Portfolio X-Ray
              </li>
            </ul>
            {currentTier === "miner" ? (
              <Button
                variant="secondary"
                size="lg"
                className="w-full"
                onClick={handleManageBilling}
              >
                Manage Subscription
              </Button>
            ) : (
              <Button
                variant="secondary"
                size="lg"
                className="w-full"
                onClick={() => handleSubscribe("miner")}
                disabled={loadingTier === "miner"}
              >
                {loadingTier === "miner"
                  ? "Redirecting..."
                  : "Start 7-Day Free Trial"}
              </Button>
            )}
          </div>
        </div>

        {/* Feature Comparison Table */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-gradient-gold text-center mb-8">
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

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gradient-gold text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {[
              {
                q: "Can I cancel anytime?",
                a: "Yes. Cancel anytime from your billing portal. You'll keep access until the end of your billing period.",
              },
              {
                q: "What happens when my trial ends?",
                a: "After your 7-day free trial, you'll be charged automatically. Cancel before the trial ends to avoid charges.",
              },
              {
                q: "Can I switch between plans?",
                a: "Yes. Upgrade or downgrade anytime through the billing portal. Changes are prorated.",
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
