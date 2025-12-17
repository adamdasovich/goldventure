'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useCart } from '@/contexts/CartContext';
import { Button } from '@/components/ui/Button';
import { ProductBadges } from './ProductBadges';
import type { StoreProductList } from '@/types/api';

interface ProductCardProps {
  product: StoreProductList;
  showQuickAdd?: boolean;
}

export function ProductCard({ product, showQuickAdd = true }: ProductCardProps) {
  const { addItem, isLoading } = useCart();
  const [isAdding, setIsAdding] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const imageUrl = product.primary_image?.image_url || '/placeholder-product.png';
  const isOnSale = product.is_on_sale && product.compare_at_price_cents;
  // High-value items (over $5000) show "Inquire" instead of "Add to Cart"
  const requiresInquiry = product.price_cents >= 500000;

  const handleQuickAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (requiresInquiry) return;

    try {
      setIsAdding(true);
      await addItem(product.id);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <Link
      href={`/store/product/${product.slug}`}
      className="group block"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="glass-card rounded-xl overflow-hidden transition-all duration-300 hover:shadow-gold hover:border-gold-500/30">
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden bg-slate-800/50">
          <Image
            src={imageUrl}
            alt={product.name}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
          />

          {/* Badges Overlay */}
          <div className="absolute top-3 left-3">
            <ProductBadges badges={product.badges} />
          </div>

          {/* Out of Stock Overlay */}
          {!product.in_stock && (
            <div className="absolute inset-0 bg-slate-900/70 flex items-center justify-center">
              <span className="text-slate-300 font-medium px-4 py-2 bg-slate-800/80 rounded-lg">
                Out of Stock
              </span>
            </div>
          )}

          {/* Quick Add Button */}
          {showQuickAdd && product.in_stock && !requiresInquiry && (
            <div
              className={`absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-slate-900 to-transparent transition-opacity duration-300 ${
                isHovered ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                onClick={handleQuickAdd}
                disabled={isAdding || isLoading}
              >
                {isAdding ? 'Adding...' : 'Add to Cart'}
              </Button>
            </div>
          )}

          {/* Inquire Button for high-value items */}
          {showQuickAdd && product.in_stock && requiresInquiry && (
            <div
              className={`absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-slate-900 to-transparent transition-opacity duration-300 ${
                isHovered ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <Button variant="secondary" size="sm" className="w-full">
                Inquire
              </Button>
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="p-4">
          {/* Category */}
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
            {product.category_name}
          </p>

          {/* Title */}
          <h3 className="font-semibold text-slate-100 group-hover:text-gold-400 transition-colors line-clamp-2 mb-2">
            {product.name}
          </h3>

          {/* Description */}
          {product.short_description && (
            <p className="text-sm text-slate-400 line-clamp-2 mb-3">
              {product.short_description}
            </p>
          )}

          {/* Price */}
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-gold-400">
              ${product.price_dollars.toFixed(2)}
            </span>
            {isOnSale && product.compare_at_price_dollars && (
              <span className="text-sm text-slate-500 line-through">
                ${product.compare_at_price_dollars.toFixed(2)}
              </span>
            )}
          </div>

          {/* Sales Count */}
          {product.total_sold > 0 && (
            <p className="text-xs text-slate-500 mt-2">
              {product.total_sold} sold
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
