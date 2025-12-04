'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { metalsAPI, type MetalPrice } from '@/lib/api';
import MetalChart from '@/components/MetalChart';
import LogoMono from '@/components/LogoMono';

export default function MetalsPage() {
  const [metals, setMetals] = useState<MetalPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [selectedMetal, setSelectedMetal] = useState<string>('XAU');
  const [selectedTimeRange, setSelectedTimeRange] = useState<number>(30);

  useEffect(() => {
    fetchMetalPrices();
  }, []);

  const fetchMetalPrices = async () => {
    try {
      setLoading(true);
      const response = await metalsAPI.getPrices();
      setMetals(response.metals);
      setLastUpdated(new Date(response.timestamp).toLocaleString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metal prices');
    } finally {
      setLoading(false);
    }
  };

  const getMetalColor = (symbol: string) => {
    const colors: Record<string, string> = {
      'XAU': '#d4af37', // Gold
      'XAG': '#c0c0c0', // Silver
      'XPT': '#e5e4e2', // Platinum
      'XPD': '#cbc8c8'  // Palladium
    };
    return colors[symbol] || '#d4af37';
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '---';
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatChange = (change: number) => {
    if (change === 0) return '---';
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <div className="cursor-pointer" onClick={() => window.location.href = '/'}>
                <LogoMono className="h-18" />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">AI-Powered</Badge>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Home</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Companies</Button>
              <Button variant="primary" size="sm" onClick={() => window.location.href = '/'}>Metals</Button>
              <Button variant="ghost" size="sm">Sign In</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-6">
            Real-Time Market Data
          </Badge>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
            Precious Metals Prices
          </h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-12 animate-slide-in-up">
            Track real-time and historical prices for gold, silver, and other precious metals
          </p>
        </div>
      </section>

      {/* Real-Time Prices Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gold-400 mb-4">Current Metal Prices</h2>
            <p className="text-slate-300 text-lg mb-2">
              Live pricing data updated in real-time
            </p>
            {lastUpdated && (
              <p className="text-sm text-slate-400">
                Last updated: {lastUpdated}
              </p>
            )}
            {error && (
              <p className="text-sm text-red-400 mt-2">
                {error}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {loading ? (
              // Loading state
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
            ) : (
              // Actual data
              metals.map((metal, idx) => (
                <Card key={metal.symbol} variant="glass-card" className="text-center animate-slide-in-up" style={{ animationDelay: `${idx * 100}ms` }}>
                  <CardContent className="py-8">
                    {/* Metal Icon/Circle */}
                    <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center border-2"
                         style={{ borderColor: getMetalColor(metal.symbol), backgroundColor: `${getMetalColor(metal.symbol)}20` }}>
                      <div className="text-2xl font-bold" style={{ color: getMetalColor(metal.symbol) }}>
                        {metal.symbol}
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-gold-400 mb-1">{metal.metal}</h3>
                    <div className="text-sm text-slate-400 mb-4">{metal.symbol}/USD per {metal.unit}</div>
                    {metal.price !== null ? (
                      <>
                        <div className="text-3xl font-bold text-white mb-2">${formatPrice(metal.price)}</div>
                        <div className={`text-sm ${metal.change_percent > 0 ? 'text-green-400' : metal.change_percent < 0 ? 'text-red-400' : 'text-slate-400'}`}>
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
              ))
            )}
          </div>

          <div className="text-center mt-8">
            <Button variant="secondary" size="sm" onClick={fetchMetalPrices} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Prices'}
            </Button>
          </div>
        </div>
      </section>

      {/* Historical Data Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gold-400 mb-4">Historical Data</h2>
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
                  {metals.length > 0 && metals.map(metal => (
                    <Button
                      key={metal.symbol}
                      variant={selectedMetal === metal.symbol ? 'primary' : 'secondary'}
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
                  { label: '1W', days: 7 },
                  { label: '1M', days: 30 },
                  { label: '3M', days: 90 },
                  { label: '6M', days: 180 },
                  { label: '1Y', days: 365 }
                ].map(range => (
                  <Button
                    key={range.days}
                    variant={selectedTimeRange === range.days ? 'primary' : 'secondary'}
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

      {/* Market Insights Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gold-400 mb-4">Market Insights</h2>
            <p className="text-slate-300 text-lg">
              Key metrics and market information
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card variant="glass-card" className="text-center">
              <CardContent className="py-8">
                <div className="w-12 h-12 rounded-lg mx-auto mb-4 flex items-center justify-center"
                     style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                  <svg className="w-6 h-6" style={{ color: '#d4af37' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gold-400 mb-2">Gold/Silver Ratio</h3>
                <p className="text-2xl text-white font-bold">
                  {metals.length > 0 && metals[0].price && metals[1].price
                    ? (metals[0].price / metals[1].price).toFixed(2)
                    : '---'}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  Ounces of silver per ounce of gold
                </p>
              </CardContent>
            </Card>

            <Card variant="glass-card" className="text-center">
              <CardContent className="py-8">
                <div className="w-12 h-12 rounded-lg mx-auto mb-4 flex items-center justify-center"
                     style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                  <svg className="w-6 h-6" style={{ color: '#d4af37' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gold-400 mb-2">Total Market Value</h3>
                <p className="text-2xl text-white font-bold">
                  {metals.length > 0 && metals.every(m => m.price)
                    ? `$${(metals.reduce((sum, m) => sum + (m.price || 0), 0)).toLocaleString()}`
                    : '---'}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  Combined price per ounce (all 4 metals)
                </p>
              </CardContent>
            </Card>

            <Card variant="glass-card" className="text-center">
              <CardContent className="py-8">
                <div className="w-12 h-12 rounded-lg mx-auto mb-4 flex items-center justify-center"
                     style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                  <svg className="w-6 h-6" style={{ color: '#d4af37' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gold-400 mb-2">Most Valuable</h3>
                <p className="text-2xl text-white font-bold">
                  {metals.length > 0 && metals.every(m => m.price)
                    ? metals.reduce((max, m) => (m.price || 0) > (max.price || 0) ? m : max, metals[0]).metal
                    : '---'}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  Highest price per ounce
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Additional Info */}
          <div className="mt-12 text-center">
            <Card variant="glass-card" className="max-w-2xl mx-auto">
              <CardContent className="py-6">
                <h4 className="text-lg font-semibold text-gold-400 mb-3">About These Prices</h4>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Precious metals prices are provided by Alpha Vantage and represent the spot price
                  in USD per troy ounce. Prices are updated in real-time during market hours and cached
                  for 5 minutes to optimize API usage. Historical data includes up to 1 year of daily
                  closing prices.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
