"use client";

import { useState, useEffect, useCallback } from "react";
import { metalsAPI, type MetalPrice } from "@/lib/api";

export default function MetalsTicker() {
  const [metals, setMetals] = useState<MetalPrice[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [error, setError] = useState(false);

  const fetchPrices = useCallback(async () => {
    try {
      const data = await metalsAPI.getPrices();
      // Filter to gold, silver, and optionally copper/platinum
      const priority = ["XAU", "XAG", "XPT"];
      const filtered = data.metals
        .filter((m) => priority.includes(m.symbol))
        .sort(
          (a, b) => priority.indexOf(a.symbol) - priority.indexOf(b.symbol),
        );
      setMetals(filtered.length > 0 ? filtered : data.metals.slice(0, 3));
      setLastUpdated(data.timestamp);
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, 30000);
    return () => clearInterval(interval);
  }, [fetchPrices]);

  if (error || metals.length === 0) return null;

  const formatPrice = (price: number | null) => {
    if (!price) return "—";
    return price >= 100
      ? `$${price.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
      : `$${price.toFixed(2)}`;
  };

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="flex items-center gap-4 sm:gap-6 overflow-x-auto py-1 scrollbar-none">
      {metals.map((m) => (
        <div key={m.symbol} className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs font-semibold text-slate-400">
            {m.metal}
          </span>
          <span className="text-sm font-bold text-slate-200">
            {formatPrice(m.price)}
          </span>
          <span
            className={`text-xs font-medium flex items-center gap-0.5 ${
              m.change_percent >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {m.change_percent >= 0 ? (
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 17l5-5 5 5"
                />
              </svg>
            ) : (
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 7l-5 5-5-5"
                />
              </svg>
            )}
            {Math.abs(m.change_percent).toFixed(2)}%
          </span>
        </div>
      ))}
      {lastUpdated && (
        <span className="text-[10px] text-slate-600 flex-shrink-0 ml-auto">
          Updated {formatTime(lastUpdated)}
        </span>
      )}
    </div>
  );
}
