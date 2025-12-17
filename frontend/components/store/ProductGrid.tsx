'use client';

import React from 'react';
import { ProductCard } from './ProductCard';
import type { StoreProductList } from '@/types/api';

interface ProductGridProps {
  products: StoreProductList[];
  columns?: 2 | 3 | 4;
  showQuickAdd?: boolean;
  emptyMessage?: string;
}

export function ProductGrid({
  products,
  columns = 4,
  showQuickAdd = true,
  emptyMessage = 'No products found',
}: ProductGridProps) {
  const gridCols = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  };

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-slate-400 text-lg">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={`grid ${gridCols[columns]} gap-6`}>
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          showQuickAdd={showQuickAdd}
        />
      ))}
    </div>
  );
}
