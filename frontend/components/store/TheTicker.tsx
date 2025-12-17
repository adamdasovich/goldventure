'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { storeAPI } from '@/lib/api';
import type { StoreRecentPurchase } from '@/types/api';

interface TheTickerProps {
  variant?: 'sidebar' | 'banner';
  limit?: number;
  refreshInterval?: number; // in milliseconds
}

export function TheTicker({
  variant = 'sidebar',
  limit = 5,
  refreshInterval = 30000,
}: TheTickerProps) {
  const [purchases, setPurchases] = useState<StoreRecentPurchase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newPurchaseId, setNewPurchaseId] = useState<number | null>(null);

  useEffect(() => {
    const fetchPurchases = async () => {
      try {
        const response = await storeAPI.ticker.getRecent(limit);
        // Handle both array response and paginated response with results
        const newPurchases = Array.isArray(response) ? response : (response.results || []);

        // Check if there's a new purchase
        if (purchases.length > 0 && newPurchases.length > 0) {
          const latestId = newPurchases[0].id;
          if (latestId !== purchases[0]?.id) {
            setNewPurchaseId(latestId);
            setTimeout(() => setNewPurchaseId(null), 3000);
          }
        }

        setPurchases(newPurchases);
      } catch (error) {
        console.error('Failed to fetch ticker:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPurchases();
    const interval = setInterval(fetchPurchases, refreshInterval);

    return () => clearInterval(interval);
  }, [limit, refreshInterval]);

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (isLoading) {
    return (
      <div className={variant === 'sidebar' ? 'p-4' : 'py-2 px-4'}>
        <div className="animate-pulse space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 bg-slate-800/50 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (purchases.length === 0) {
    return null;
  }

  if (variant === 'banner') {
    const latestPurchase = purchases[0];
    return (
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-gold-500/20 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-sm">
          <span className="animate-pulse text-gold-400">●</span>
          <span className="text-slate-400">
            {latestPurchase.is_anonymous ? 'A collector' : latestPurchase.location} just acquired
          </span>
          <Link
            href={`/store/product/${latestPurchase.product_slug}`}
            className="font-medium text-gold-400 hover:text-gold-300 transition-colors"
          >
            {latestPurchase.product_name}
          </Link>
          <span className="text-slate-500">•</span>
          <span className="text-slate-500">{formatTimeAgo(latestPurchase.created_at)}</span>
        </div>
      </div>
    );
  }

  // Sidebar variant
  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="animate-pulse text-gold-400 text-lg">●</span>
        <h3 className="font-semibold text-slate-100">The Ticker</h3>
      </div>

      <div className="space-y-3">
        {purchases.map((purchase) => (
          <div
            key={purchase.id}
            className={`p-3 rounded-lg transition-all duration-500 ${
              purchase.id === newPurchaseId
                ? 'bg-gold-500/20 border border-gold-500/30 animate-pulse'
                : 'bg-slate-800/30'
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Product thumbnail */}
              {purchase.product_image && (
                <div className="w-10 h-10 rounded bg-slate-700 flex-shrink-0 overflow-hidden">
                  <img
                    src={purchase.product_image}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-400">
                  {purchase.is_anonymous ? 'A collector' : `Collector in ${purchase.location}`}
                </p>
                <Link
                  href={`/store/product/${purchase.product_slug}`}
                  className="text-sm font-medium text-slate-200 hover:text-gold-400 transition-colors line-clamp-1"
                >
                  {purchase.product_name}
                </Link>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-medium text-gold-400">
                    ${purchase.amount_dollars.toFixed(0)}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatTimeAgo(purchase.created_at)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Link
        href="/store"
        className="block mt-4 text-center text-sm text-slate-400 hover:text-gold-400 transition-colors"
      >
        View All Products →
      </Link>
    </div>
  );
}
