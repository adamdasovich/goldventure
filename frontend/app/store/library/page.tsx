'use client';

import React, { useEffect, useState } from 'react';
import { storeAPI, StoreProductFilters } from '@/lib/api';
import { ProductGrid } from '@/components/store';
import { Button } from '@/components/ui/Button';
import type { StoreProductList } from '@/types/api';

const CATEGORY_SLUG = 'resource-library';

export default function LibraryPage() {
  const [products, setProducts] = useState<StoreProductList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<StoreProductFilters['ordering']>('-created_at');
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
        console.error('Failed to fetch library products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [sortBy, productType]);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-900/50 via-slate-900 to-slate-900 border border-blue-500/20 p-8 lg:p-12">
        <div className="relative z-10">
          <div className="mb-4">
            <svg className="w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Resource Library
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl">
            Educational materials, geological maps, reports, and digital downloads for serious students of mining and geology.
          </p>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
      </section>

      {/* Filters & Sort */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={productType === 'all' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('all')}
          >
            All Resources
          </Button>
          <Button
            variant={productType === 'digital' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('digital')}
            className="inline-flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Digital Downloads
          </Button>
          <Button
            variant={productType === 'physical' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('physical')}
            className="inline-flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Physical Books
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
          emptyMessage="No resources available yet. Check back soon!"
        />
      )}

      {/* Resource Categories */}
      <section className="grid md:grid-cols-3 gap-6 pt-8">
        <div className="glass rounded-xl p-6 border border-slate-700">
          <div className="mb-3">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Geological Maps</h3>
          <p className="text-sm text-slate-400">
            High-resolution digital maps of mining districts, geological surveys, and claim boundaries.
          </p>
        </div>
        <div className="glass rounded-xl p-6 border border-slate-700">
          <div className="mb-3">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Technical Reports</h3>
          <p className="text-sm text-slate-400">
            Historic assay reports, NI 43-101 summaries, and technical analysis documents.
          </p>
        </div>
        <div className="glass rounded-xl p-6 border border-slate-700">
          <div className="mb-3">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M12 14l9-5-9-5-9 5 9 5z" />
              <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Educational Guides</h3>
          <p className="text-sm text-slate-400">
            Courses, tutorials, and guides for prospecting, geology, and mining investment.
          </p>
        </div>
      </section>

      {/* Digital Download Info */}
      <section className="glass rounded-xl p-6 border border-blue-500/20 bg-gradient-to-r from-blue-900/20 to-slate-900">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100 mb-2">Instant Digital Downloads</h3>
            <p className="text-slate-400">
              Purchase digital resources and receive immediate access. Download links are sent to your email and available in your account for 72 hours.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
