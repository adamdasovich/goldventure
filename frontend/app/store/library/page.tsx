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
          <span className="text-5xl mb-4 block">📚</span>
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
          >
            ⬇️ Digital Downloads
          </Button>
          <Button
            variant={productType === 'physical' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setProductType('physical')}
          >
            📖 Physical Books
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
          <div className="text-3xl mb-3">🗺️</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Geological Maps</h3>
          <p className="text-sm text-slate-400">
            High-resolution digital maps of mining districts, geological surveys, and claim boundaries.
          </p>
        </div>
        <div className="glass rounded-xl p-6 border border-slate-700">
          <div className="text-3xl mb-3">📊</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Technical Reports</h3>
          <p className="text-sm text-slate-400">
            Historic assay reports, NI 43-101 summaries, and technical analysis documents.
          </p>
        </div>
        <div className="glass rounded-xl p-6 border border-slate-700">
          <div className="text-3xl mb-3">🎓</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2">Educational Guides</h3>
          <p className="text-sm text-slate-400">
            Courses, tutorials, and guides for prospecting, geology, and mining investment.
          </p>
        </div>
      </section>

      {/* Digital Download Info */}
      <section className="glass rounded-xl p-6 border border-blue-500/20 bg-gradient-to-r from-blue-900/20 to-slate-900">
        <div className="flex items-start gap-4">
          <div className="text-4xl">⚡</div>
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
