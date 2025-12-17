'use client';

import React, { useEffect, useState } from 'react';
import { storeAPI, StoreProductFilters } from '@/lib/api';
import { ProductGrid } from '@/components/store';
import { Button } from '@/components/ui/Button';
import type { StoreProductList } from '@/types/api';

const CATEGORY_SLUG = 'field-gear';

export default function GearPage() {
  const [products, setProducts] = useState<StoreProductList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<StoreProductFilters['ordering']>('-total_sold');
  const [productType, setProductType] = useState<'all' | 'physical' | 'digital'>('all');

  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        const filters: StoreProductFilters = {
          category: CATEGORY_SLUG,
          ordering: sortBy,
        };
        if (productType !== 'all') {
          filters.product_type = productType;
        }
        const response = await storeAPI.products.getAll(filters);
        setProducts(response.results);
      } catch (error) {
        console.error('Failed to fetch gear products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [sortBy, productType]);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-copper-900/50 via-slate-900 to-slate-900 border border-copper-500/20 p-8 lg:p-12">
        <div className="relative z-10">
          <div className="mb-4">
            <svg className="w-12 h-12 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Field Gear
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl">
            Essential equipment, apparel, and tools for prospectors, geologists, and mining enthusiasts.
          </p>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-copper-500/10 rounded-full blur-3xl" />
      </section>

      {/* Filters & Sort */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={productType === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('all')}
          >
            All Items
          </Button>
          <Button
            variant={productType === 'physical' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('physical')}
          >
            Physical
          </Button>
          <Button
            variant={productType === 'digital' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('digital')}
          >
            Digital
          </Button>
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as StoreProductFilters['ordering'])}
          className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
        >
          <option value="-total_sold">Most Popular</option>
          <option value="-created_at">Newest</option>
          <option value="price_cents">Price: Low to High</option>
          <option value="-price_cents">Price: High to Low</option>
        </select>
      </div>

      {/* Products Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
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
          columns={4}
          emptyMessage="No gear available yet. Check back soon!"
        />
      )}

      {/* Featured Collections */}
      <section className="grid md:grid-cols-2 gap-6 pt-8">
        <div className="glass rounded-xl p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-slate-100 mb-2">Stake Your Claim Collection</h3>
          <p className="text-slate-400 mb-4">
            Our signature apparel line for the modern prospector. High-quality, durable, and designed for the field.
          </p>
          <Button variant="secondary" size="sm">
            View Collection
          </Button>
        </div>
        <div className="glass rounded-xl p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-slate-100 mb-2">Geologist Starter Kits</h3>
          <p className="text-slate-400 mb-4">
            Everything you need to start your geological exploration journey. Curated by experts.
          </p>
          <Button variant="secondary" size="sm">
            View Kits
          </Button>
        </div>
      </section>
    </div>
  );
}
