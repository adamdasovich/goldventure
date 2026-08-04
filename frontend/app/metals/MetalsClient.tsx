"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { metalsAPI, type MetalPrice } from "@/lib/api";
import MetalChart from "@/components/MetalChart";
import LogoMono from "@/components/LogoMono";

interface MetalsClientProps {
  initialMetals?: MetalPrice[];
  initialTimestamp?: string;
}

export default function MetalsClient({
  initialMetals,
  initialTimestamp,
}: MetalsClientProps) {
  const hasInitial = !!(initialMetals && initialMetals.length);
  const [metals, setMetals] = useState<MetalPrice[]>(initialMetals ?? []);
  const [loading, setLoading] = useState(!hasInitial);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [selectedMetal, setSelectedMetal] = useState<string>("XAU");
  const [selectedTimeRange, setSelectedTimeRange] = useState<number>(30);

  useEffect(() => {
    // Format the server-provided timestamp on the client only — formatting it
    // during SSR would risk a timezone hydration mismatch.
    if (initialTimestamp) {
      setLastUpdated(new Date(initialTimestamp).toLocaleString());
    }
    // Refresh to live data on mount. Silent when the server already seeded
    // prices, so the cards don't flash back to skeletons after hydration.
    fetchMetalPrices({ silent: hasInitial });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchMetalPrices = async ({
    silent = false,
  }: { silent?: boolean } = {}) => {
    try {
      if (!silent) setLoading(true);
      const response = await metalsAPI.getPrices();
      setMetals(response.metals);
      setLastUpdated(new Date(response.timestamp).toLocaleString());
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch metal prices",
      );
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const getMetalColor = (symbol: string) => {
    const colors: Record<string, string> = {
      XAU: "#d4af37", // Gold
      XAG: "#c0c0c0", // Silver
      XPT: "#e5e4e2", // Platinum
      XPD: "#cbc8c8", // Palladium
      CU: "#b87333", // Copper
      NI: "#8fa9b8", // Nickel
      LI: "#cc66cc", // Lithium
      CO: "#3b6fb5", // Cobalt
      REE: "#5fae8c", // Rare Earth Elements
      U: "#6abf4b", // Uranium
    };
    return colors[symbol] || "#d4af37";
  };

  // Precious metals fill the 4-card grid; base/critical minerals (copper,
  // etc.) render in their own section.
  const preciousMetals = metals.filter(
    (m) => (m.category ?? "precious") === "precious",
  );
  const baseMetals = metals.filter(
    (m) => m.category && m.category !== "precious",
  );

  const handleMetalClick = (symbol: string) => {
    setSelectedMetal(symbol);
    document
      .getElementById("historical-data")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  const renderMetalCard = (metal: MetalPrice, idx: number) => (
    <Card
      key={metal.symbol}
      variant="glass-card"
      className="text-center animate-slide-in-up cursor-pointer transition-transform hover:scale-105"
      style={{ animationDelay: `${idx * 100}ms` }}
      onClick={() => handleMetalClick(metal.symbol)}
    >
      <CardContent className="py-8">
        {/* Metal Icon/Circle */}
        <div
          className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center border-2"
          style={{
            borderColor: getMetalColor(metal.symbol),
            backgroundColor: `${getMetalColor(metal.symbol)}20`,
          }}
        >
          <div
            className="text-2xl font-bold"
            style={{ color: getMetalColor(metal.symbol) }}
          >
            {metal.symbol}
          </div>
        </div>
        <h3 className="text-2xl font-bold text-gold-400 mb-1">{metal.metal}</h3>
        <div className="text-sm text-slate-400 mb-4">
          {metal.symbol}/USD per {metal.unit}
        </div>
        {metal.price !== null ? (
          <>
            <div className="text-3xl font-bold text-white mb-2">
              ${formatPrice(metal.price)}
            </div>
            <div
              className={`text-sm ${metal.change_percent > 0 ? "text-green-400" : metal.change_percent < 0 ? "text-red-400" : "text-slate-400"}`}
            >
              {formatChange(metal.change_percent)}
            </div>
          </>
        ) : (
          <>
            <div className="text-lg text-red-400 mb-2">Error</div>
            <div className="text-xs text-slate-400">{metal.error}</div>
          </>
        )}
      </CardContent>
    </Card>
  );

  const formatPrice = (price: number | null) => {
    if (price === null) return "---";
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const formatChange = (change: number) => {
    if (change === 0) return "---";
    const sign = change > 0 ? "+" : "";
    return `${sign}${change.toFixed(2)}%`;
  };
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <div
                className="cursor-pointer"
                onClick={() => (window.location.href = "/")}
              >
                <LogoMono className="h-18" />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => (window.location.href = "/")}
              >
                Home
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => (window.location.href = "/")}
              >
                Dashboard
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => (window.location.href = "/")}
              >
                Companies
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => (window.location.href = "/")}
              >
                Metals
              </Button>
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page header — server-rendered H1 + intro for SEO */}
      <header className="pt-14 pb-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            Live Precious &amp; Critical Metals Prices
          </h1>
          <p className="text-lg text-slate-300 leading-relaxed">
            Real-time spot prices for gold, silver, platinum and palladium,
            alongside the base and critical minerals that drive junior mining —
            copper, nickel, lithium, cobalt, uranium and rare earths. Track live
            pricing and historical trends across the metals that move the
            exploration sector.
          </p>
        </div>
      </header>

      {/* Real-Time Prices Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-gold-400 mb-4">
              Precious Metal Prices
            </h2>
            <p className="text-slate-300 text-lg mb-2">
              Live pricing data updated in real-time
            </p>
            {lastUpdated && (
              <p className="text-sm text-slate-400">
                Last updated: {lastUpdated}
              </p>
            )}
            {error && <p className="text-sm text-red-400 mt-2">{error}</p>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {loading
              ? // Loading state
                Array.from({ length: 4 }).map((_, idx) => (
                  <Card key={idx} variant="glass-card" className="text-center">
                    <CardContent className="py-8">
                      <div className="w-16 h-16 rounded-full bg-slate-700 mx-auto mb-4 animate-pulse"></div>
                      <div className="h-6 bg-slate-700 rounded w-24 mx-auto mb-2 animate-pulse"></div>
                      <div className="h-4 bg-slate-700 rounded w-16 mx-auto mb-4 animate-pulse"></div>
                      <div className="h-8 bg-slate-700 rounded w-32 mx-auto mb-2 animate-pulse"></div>
                      <div className="h-4 bg-slate-700 rounded w-20 mx-auto animate-pulse"></div>
                    </CardContent>
                  </Card>
                ))
              : // Actual data — precious metals only
                preciousMetals.map((metal, idx) => renderMetalCard(metal, idx))}
          </div>

          {/* Base & Critical Minerals */}
          {!loading && baseMetals.length > 0 && (
            <div className="mt-12">
              <h2 className="text-2xl font-bold text-gold-400 mb-6 text-center">
                Base &amp; Critical Minerals
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {baseMetals.map((metal, idx) => renderMetalCard(metal, idx))}
              </div>
            </div>
          )}

          <div className="text-center mt-8">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fetchMetalPrices()}
              disabled={loading}
            >
              {loading ? "Refreshing..." : "Refresh Prices"}
            </Button>
          </div>
        </div>
      </section>

      {/* Historical Data Section */}
      <section id="historical-data" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gold-400 mb-4">
              Historical Data
            </h2>
            <p className="text-slate-300 text-lg mb-8">
              Analyze price trends and historical performance
            </p>
          </div>

          <Card variant="glass-strong" className="max-w-6xl mx-auto">
            <CardHeader>
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <CardTitle>Price Charts</CardTitle>
                  <CardDescription>
                    Historical price data and trends for precious metals
                  </CardDescription>
                </div>

                {/* Metal Selector */}
                <div className="flex gap-2">
                  {metals.length > 0 &&
                    metals.map((metal) => (
                      <Button
                        key={metal.symbol}
                        variant={
                          selectedMetal === metal.symbol
                            ? "primary"
                            : "secondary"
                        }
                        size="sm"
                        onClick={() => setSelectedMetal(metal.symbol)}
                      >
                        {metal.metal}
                      </Button>
                    ))}
                </div>
              </div>
            </CardHeader>
            <CardContent className="py-6">
              {/* Chart */}
              <MetalChart symbol={selectedMetal} days={selectedTimeRange} />

              {/* Time Range Selector */}
              <div className="flex gap-2 justify-center mt-6">
                {[
                  { label: "1W", days: 7 },
                  { label: "1M", days: 30 },
                  { label: "3M", days: 90 },
                  { label: "6M", days: 180 },
                  { label: "1Y", days: 365 },
                ].map((range) => (
                  <Button
                    key={range.days}
                    variant={
                      selectedTimeRange === range.days ? "primary" : "secondary"
                    }
                    size="sm"
                    onClick={() => setSelectedTimeRange(range.days)}
                  >
                    {range.label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
