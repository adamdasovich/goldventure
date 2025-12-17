'use client';

import React, { useEffect, useState } from 'react';
import { storeAPI, StoreProductFilters } from '@/lib/api';
import { ProductGrid } from '@/components/store';
import { TheTicker } from '@/components/store/TheTicker';
import { Button } from '@/components/ui/Button';
import type { StoreProductList } from '@/types/api';

const CATEGORY_SLUG = 'vault';

export default function VaultPage() {
  const [products, setProducts] = useState<StoreProductList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<StoreProductFilters['ordering']>('-created_at');
  const [filterBadge, setFilterBadge] = useState<string>('');

  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        const filters: StoreProductFilters = {
          category: CATEGORY_SLUG,
          ordering: sortBy,
        };
        if (filterBadge) {
          filters.badge = filterBadge;
        }
        const response = await storeAPI.products.getAll(filters);
        setProducts(response.results);
      } catch (error) {
        console.error('Failed to fetch vault products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [sortBy, filterBadge]);

  return (
    <div className="grid lg:grid-cols-4 gap-8">
      {/* Main Content */}
      <div className="lg:col-span-3 space-y-8">
        {/* Hero Section */}
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-900/50 via-slate-900 to-slate-900 border border-purple-500/20 p-8 lg:p-12">
          <div className="relative z-10">
            <div className="mb-4">
              <svg className="w-12 h-12 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
              The Vault
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl">
              Rare specimens, collectible bullion, and premium geological artifacts. Each piece authenticated and documented.
            </p>
          </div>
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gold-500/10 rounded-full blur-3xl" />
        </section>

        {/* Filters & Sort */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filterBadge === '' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterBadge('')}
            >
              All
            </Button>
            <Button
              variant={filterBadge === 'rare' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterBadge('rare')}
              className="inline-flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              Rare
            </Button>
            <Button
              variant={filterBadge === 'limited_edition' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterBadge('limited_edition')}
              className="inline-flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Limited Edition
            </Button>
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as StoreProductFilters['ordering'])}
            className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
          >
            <option value="-created_at">Newest</option>
            <option value="-total_sold">Most Popular</option>
            <option value="price_cents">Price: Low to High</option>
            <option value="-price_cents">Price: High to Low</option>
          </select>
        </div>

        {/* Products Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="glass-card rounded-xl p-4 animate-pulse">
                <div className="aspect-square bg-slate-800 rounded-lg mb-4" />
                <div className="h-4 bg-slate-800 rounded mb-2" />
                <div className="h-4 bg-slate-800 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <ProductGrid
            products={products}
            columns={3}
            emptyMessage="No items in The Vault yet. Check back soon!"
          />
        )}
      </div>

      {/* Sidebar */}
      <aside className="space-y-6">
        <TheTicker variant="sidebar" limit={5} />

        {/* Collection Info */}
        <div className="glass rounded-xl p-4">
          <h3 className="font-semibold text-slate-100 mb-3">About The Vault</h3>
          <div className="space-y-3 text-sm text-slate-400">
            <p>
              Each item in The Vault has been carefully curated and authenticated by our team of geologists and collectors.
            </p>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Certificate of Authenticity</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Provenance Documentation</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Secure Packaging & Insurance</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
