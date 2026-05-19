"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";

interface UpgradeModalProps {
  onClose: () => void;
  feature: string;
  requiredTier?: "prospector" | "miner";
}

export default function UpgradeModal({
  onClose,
  feature,
  requiredTier = "prospector",
}: UpgradeModalProps) {
  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative glass-strong rounded-2xl max-w-md w-full p-6 animate-slide-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
          aria-label="Close"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Icon */}
        <div className="w-14 h-14 rounded-full bg-gold-500/15 border border-gold-500/30 flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-7 h-7 text-gold-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>

        <h3 className="text-xl font-bold text-white text-center mb-2">
          Upgrade to Unlock
        </h3>
        <p className="text-slate-400 text-center text-sm mb-6">
          <strong className="text-gold-400">{feature}</strong> is available on
          the {requiredTier === "miner" ? "Miner" : "Prospector"} plan and
          above. Upgrade to get full access.
        </p>

        <div className="space-y-3">
          <Link href="/pricing" className="block">
            <Button variant="primary" size="lg" className="w-full cta-glow">
              View Plans &amp; Pricing
            </Button>
          </Link>
          <button
            onClick={onClose}
            className="w-full text-sm text-slate-400 hover:text-slate-300 transition-colors py-2"
          >
            Maybe later
          </button>
        </div>

        {/* Value props */}
        <div className="mt-6 pt-4 border-t border-slate-700/50">
          <p className="text-xs text-slate-500 text-center mb-3">
            Start with a 7-day free trial
          </p>
          <div className="flex justify-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <svg
                className="w-3.5 h-3.5 text-emerald-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              Cancel anytime
            </span>
            <span className="flex items-center gap-1">
              <svg
                className="w-3.5 h-3.5 text-emerald-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              Secure payments
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
