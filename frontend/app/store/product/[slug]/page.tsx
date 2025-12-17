'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { storeAPI } from '@/lib/api';
import { ProductDetail, ProductGrid } from '@/components/store';
import type { StoreProductDetail as ProductDetailType, StoreProductList } from '@/types/api';

export default function ProductPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<StoreProductList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProduct = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const productData = await storeAPI.products.getBySlug(slug);
        setProduct(productData);

        // Fetch related products from the same category
        if (productData.category?.slug) {
          const related = await storeAPI.products.getByCategory(productData.category.slug);
          // Filter out the current product and limit to 4
          setRelatedProducts(
            related.results.filter((p) => p.id !== productData.id).slice(0, 4)
          );
        }
      } catch (err) {
        console.error('Failed to fetch product:', err);
        setError('Product not found');
      } finally {
        setIsLoading(false);
      }
    };

    if (slug) {
      fetchProduct();
    }
  }, [slug]);

  if (isLoading) {
    return (
      <div className="space-y-8">
        {/* Breadcrumb skeleton */}
        <div className="h-4 bg-slate-800 rounded w-48 animate-pulse" />

        {/* Product skeleton */}
        <div className="grid lg:grid-cols-2 gap-8">
          <div className="aspect-square bg-slate-800 rounded-xl animate-pulse" />
          <div className="space-y-4">
            <div className="h-8 bg-slate-800 rounded w-3/4 animate-pulse" />
            <div className="h-4 bg-slate-800 rounded w-1/2 animate-pulse" />
            <div className="h-6 bg-slate-800 rounded w-1/4 animate-pulse" />
            <div className="h-32 bg-slate-800 rounded animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">🔍</div>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Product Not Found</h1>
        <p className="text-slate-400 mb-6">
          The product you're looking for doesn't exist or has been removed.
        </p>
        <Link
          href="/store"
          className="inline-flex items-center gap-2 text-gold-400 hover:text-gold-300 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Store
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/store" className="hover:text-gold-400 transition-colors">
          Store
        </Link>
        <span>/</span>
        <Link
          href={`/store/${product.category?.slug || ''}`}
          className="hover:text-gold-400 transition-colors"
        >
          {product.category?.name || 'Products'}
        </Link>
        <span>/</span>
        <span className="text-slate-200 truncate max-w-xs">{product.name}</span>
      </nav>

      {/* Product Detail */}
      <ProductDetail product={product} />

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <section className="border-t border-slate-700 pt-12">
          <h2 className="text-2xl font-bold text-slate-100 mb-6">
            More from {product.category?.name || 'this collection'}
          </h2>
          <ProductGrid products={relatedProducts} columns={4} />
        </section>
      )}
    </div>
  );
}
