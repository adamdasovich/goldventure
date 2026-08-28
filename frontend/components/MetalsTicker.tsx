"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  metalsAPI,
  marketAPI,
  type MetalPrice,
  type TopMover,
} from "@/lib/api";
import { companyHref } from "@/lib/companyUrl";

interface TickerItem {
  key: string;
  label: string;
  price: string;
  change: number;
  href?: string;
  isMetal?: boolean;
  /* Days the change covers. Labelled from this rather than hardcoded, so the
     strip cannot claim a period the API did not return. */
  periodDays: number;
}

export default function MetalsTicker() {
  const [items, setItems] = useState<TickerItem[]>([]);
  const [error, setError] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [metalsData, moversData] = await Promise.allSettled([
        metalsAPI.getPrices(),
        marketAPI.getTopMovers(10, 1),
      ]);

      const tickerItems: TickerItem[] = [];

      // Metals
      if (metalsData.status === "fulfilled") {
        const priority = ["XAU", "XAG", "XPT"];
        const metals = metalsData.value.metals
          .filter((m) => priority.includes(m.symbol))
          .sort(
            (a, b) => priority.indexOf(a.symbol) - priority.indexOf(b.symbol),
          );

        for (const m of metals) {
          tickerItems.push({
            key: `metal-${m.symbol}`,
            label: m.metal,
            price:
              m.price && m.price >= 100
                ? `$${m.price.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                : `$${(m.price ?? 0).toFixed(2)}`,
            change: m.change_percent,
            href: "/metals",
            isMetal: true,
            periodDays: 1,
          });
        }
      }

      // Top movers
      if (moversData.status === "fulfilled") {
        for (const m of moversData.value.movers) {
          tickerItems.push({
            key: `stock-${m.company_id}`,
            label: m.ticker || m.company_name,
            price: `$${m.price.toFixed(2)}`,
            change: m.change_percent,
            href: companyHref({ id: m.company_id, slug: m.company_slug }),
            periodDays: moversData.value.period_days ?? 1,
          });
        }
      }

      if (tickerItems.length > 0) {
        setItems(tickerItems);
        setError(false);
      }
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (error || items.length === 0) return null;

  // Duplicate items for seamless loop
  const tickerContent = [...items, ...items];

  return (
    <div className="ticker-wrap overflow-hidden" aria-label="Market ticker">
      <div className="ticker-track flex items-center gap-8">
        {tickerContent.map((item, i) => {
          const inner = (
            <span className="flex items-center gap-2 shrink-0 py-2 group">
              <span
                className={`text-xs font-semibold ${item.isMetal ? "text-gold-400" : "text-slate-400"} group-hover:text-gold-300 transition-colors`}
              >
                {item.label}
              </span>
              <span className="text-sm font-bold text-slate-200">
                {item.price}
              </span>
              {/* Both sides are a one-session change now, but the period is
                  still spelled out and comes from the item rather than a
                  literal. Metals and stocks previously carried 1-day and
                  7-day changes rendered identically, so every stock move read
                  as today's; labelling from the data means the strip cannot
                  drift out of step with the window it asked for again. */}
              <span
                className={`text-xs font-medium flex items-center gap-0.5 ${
                  item.change >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
                title={
                  item.periodDays === 1
                    ? "Change since the previous close"
                    : `Change over the past ${item.periodDays} days`
                }
              >
                {item.change >= 0 ? "\u25B2" : "\u25BC"}
                {Math.abs(item.change).toFixed(2)}%
                <span className="ml-0.5 text-[10px] text-slate-500">
                  {item.periodDays}d
                </span>
              </span>
              {/* Separator dot */}
              <span className="text-slate-700 ml-2">&middot;</span>
            </span>
          );

          return item.href ? (
            <Link
              key={`${item.key}-${i}`}
              href={item.href}
              className="shrink-0 inline-flex items-center min-h-11"
            >
              {inner}
            </Link>
          ) : (
            <span key={`${item.key}-${i}`} className="flex-shrink-0">
              {inner}
            </span>
          );
        })}
      </div>
    </div>
  );
}
