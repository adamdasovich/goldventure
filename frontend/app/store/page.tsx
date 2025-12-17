'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { storeAPI } from '@/lib/api';
import { ProductGrid } from '@/components/store';
import { Button } from '@/components/ui/Button';
import type { StoreProductList, StoreCategory } from '@/types/api';

interface SectionConfig {
  slug: string;
  title: string;
  description: string;
  href: string;
  gradient: string;
  icon: React.ReactNode;
}

const DiamondIcon = () => (
  <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

const PickaxeIcon = () => (
  <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
  </svg>
);

const LibraryIcon = () => (
  <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const sections: SectionConfig[] = [
  {
    slug: 'vault',
    title: 'The Vault',
    description: 'Rare specimens, collectible bullion, and premium geological artifacts',
    href: '/store/vault',
    gradient: 'from-purple-900/50 via-slate-900 to-slate-900',
    icon: <DiamondIcon />,
  },
  {
    slug: 'field-gear',
    title: 'Field Gear',
    description: 'Essential equipment and apparel for prospectors and geologists',
    href: '/store/field-gear',
    gradient: 'from-copper-900/50 via-slate-900 to-slate-900',
    icon: <PickaxeIcon />,
  },
  {
    slug: 'resource-library',
    title: 'Resource Library',
    description: 'Educational materials, maps, and digital downloads',
    href: '/store/resource-library',
    gradient: 'from-blue-900/50 via-slate-900 to-slate-900',
    icon: <LibraryIcon />,
  },
];

export default function StorePage() {
  const [featuredProducts, setFeaturedProducts] = useState<StoreProductList[]>([]);
  const [categories, setCategories] = useState<StoreCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, categoriesRes] = await Promise.all([
          storeAPI.products.getFeatured(),
          storeAPI.categories.getAll(),
        ]);
        // Handle both array and paginated responses
        setFeaturedProducts(Array.isArray(productsRes) ? productsRes : (productsRes.results || []));
        setCategories(Array.isArray(categoriesRes) ? categoriesRes : (categoriesRes.results || []));
      } catch (error) {
        console.error('Failed to fetch store data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl lg:text-5xl font-bold text-gradient-gold mb-4">
          The GoldVenture Store
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Rare specimens, essential gear, and premium resources for the discerning collector and prospector
        </p>
      </section>

      {/* Category Sections */}
      <section className="grid md:grid-cols-3 gap-6">
        {sections.map((section) => (
          <Link
            key={section.slug}
            href={section.href}
            className="group block"
          >
            <div className={`glass-card rounded-xl p-6 h-full bg-gradient-to-br ${section.gradient} border border-slate-700 hover:border-gold-500/50 transition-all duration-300`}>
              <div className="mb-4">{section.icon}</div>
              <h2 className="text-2xl font-bold text-slate-100 group-hover:text-gold-400 transition-colors mb-2">
                {section.title}
              </h2>
              <p className="text-slate-400 mb-4">
                {section.description}
              </p>
              <span className="text-gold-400 text-sm font-medium group-hover:translate-x-1 inline-flex items-center gap-1 transition-transform">
                Browse Collection
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </div>
          </Link>
        ))}
      </section>

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-slate-100">Featured Items</h2>
              <p className="text-slate-400 mt-1">Hand-picked selections from our collection</p>
            </div>
            <Link href="/store/vault">
              <Button variant="ghost">View All</Button>
            </Link>
          </div>
          <ProductGrid products={featuredProducts} columns={4} />
        </section>
      )}

      {/* All Categories with Products */}
      {categories.map((category) => (
        <section key={category.id}>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-slate-100">{category.name}</h2>
              {category.description && (
                <p className="text-slate-400 mt-1">{category.description}</p>
              )}
            </div>
            <Link href={`/store/${category.slug}`}>
              <Button variant="ghost">View All</Button>
            </Link>
          </div>
          <CategoryProducts categorySlug={category.slug} />
        </section>
      ))}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Loading store...</p>
        </div>
      )}
    </div>
  );
}

// Sub-component to fetch products by category
function CategoryProducts({ categorySlug }: { categorySlug: string }) {
  const [products, setProducts] = useState<StoreProductList[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await storeAPI.products.getByCategory(categorySlug);
        // Handle both array and paginated responses
        const allProducts = Array.isArray(response) ? response : (response.results || []);
        setProducts(allProducts.slice(0, 4)); // Show only 4 products
      } catch (error) {
        console.error('Failed to fetch category products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [categorySlug]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-4 animate-pulse">
            <div className="aspect-square bg-slate-800 rounded-lg mb-4" />
            <div className="h-4 bg-slate-800 rounded mb-2" />
            <div className="h-4 bg-slate-800 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <p className="text-slate-500 text-center py-8">No products in this category yet.</p>
    );
  }

  return <ProductGrid products={products} columns={4} />;
}
