'use client';

import React, { useState } from 'react';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { ProductGallery } from './ProductGallery';
import { ProductBadges } from './ProductBadges';
import { ShareToChat } from './ShareToChat';
import type { StoreProductDetail as ProductDetailType, StoreProductVariant } from '@/types/api';

interface ProductDetailProps {
  product: ProductDetailType;
}

type TabType = 'details' | 'provenance' | 'authentication';

export function ProductDetail({ product }: ProductDetailProps) {
  const { addItem, isLoading: cartLoading } = useCart();
  const { isAuthenticated } = useAuth();
  const [selectedVariant, setSelectedVariant] = useState<StoreProductVariant | null>(
    product.variants.length > 0 ? product.variants[0] : null
  );
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState<TabType>('details');
  const [isAdding, setIsAdding] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  const effectivePrice = selectedVariant?.effective_price_dollars ?? product.price_dollars;
  const isOnSale = product.is_on_sale && product.compare_at_price_cents;
  const inStock = selectedVariant ? selectedVariant.inventory_count > 0 : product.in_stock;
  const requiresInquiry = product.requires_inquiry;

  const handleAddToCart = async () => {
    try {
      setIsAdding(true);
      await addItem(product.id, selectedVariant?.id, quantity);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const tabs: { id: TabType; label: string; content: string | null }[] = [
    { id: 'details', label: 'Details', content: product.description },
    { id: 'provenance', label: 'Provenance', content: product.provenance_info },
    { id: 'authentication', label: 'Authentication', content: product.authentication_docs?.length > 0 ? 'docs' : null },
  ];

  const visibleTabs = tabs.filter((tab) => tab.content);

  return (
    <div className="grid lg:grid-cols-2 gap-8 lg:gap-12">
      {/* Left: Image Gallery */}
      <div>
        <ProductGallery images={product.images} productName={product.name} />
      </div>

      {/* Right: Product Info */}
      <div className="space-y-6">
        {/* Category & Badges */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm text-slate-400 uppercase tracking-wider">
            {product.category.name}
          </span>
          <ProductBadges badges={product.badges} />
        </div>

        {/* Title */}
        <h1 className="text-3xl lg:text-4xl font-bold text-slate-100">
          {product.name}
        </h1>

        {/* Short Description */}
        {product.short_description && (
          <p className="text-lg text-slate-400">
            {product.short_description}
          </p>
        )}

        {/* Price */}
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-bold text-gold-400">
            ${effectivePrice.toFixed(2)}
          </span>
          {isOnSale && product.compare_at_price_dollars && (
            <span className="text-xl text-slate-500 line-through">
              ${product.compare_at_price_dollars.toFixed(2)}
            </span>
          )}
        </div>

        {/* Stock Status */}
        <div className="flex items-center gap-2">
          {inStock ? (
            <>
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-sm text-green-400">In Stock</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-sm text-red-400">Out of Stock</span>
            </>
          )}
          {product.product_type === 'digital' && (
            <span className="text-sm text-blue-400 ml-2">• Instant Download</span>
          )}

          {/* Share Button */}
          <button
            type="button"
            onClick={() => setShowShareModal(true)}
            className="ml-auto p-2 text-slate-400 hover:text-gold-400 transition-colors"
            title="Share to Chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
        </div>

        {/* Variants */}
        {product.variants.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Options
            </label>
            <div className="flex flex-wrap gap-2">
              {product.variants.map((variant) => (
                <button
                  key={variant.id}
                  onClick={() => setSelectedVariant(variant)}
                  disabled={!variant.is_active || variant.inventory_count === 0}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    selectedVariant?.id === variant.id
                      ? 'border-gold-500 bg-gold-500/20 text-gold-400'
                      : 'border-slate-600 text-slate-300 hover:border-slate-500'
                  } ${
                    !variant.is_active || variant.inventory_count === 0
                      ? 'opacity-50 cursor-not-allowed'
                      : ''
                  }`}
                >
                  {variant.name}
                  {variant.price_cents_override && (
                    <span className="ml-1 text-sm">
                      (${variant.effective_price_dollars.toFixed(2)})
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Quantity & Add to Cart */}
        {!requiresInquiry && inStock && (
          <div className="flex items-center gap-4">
            {/* Quantity Selector */}
            <div className="flex items-center border border-slate-600 rounded-lg">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="px-3 py-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <span className="px-4 py-2 text-slate-200 font-medium min-w-[3rem] text-center">
                {quantity}
              </span>
              <button
                onClick={() => setQuantity((q) => q + 1)}
                className="px-3 py-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            {/* Add to Cart Button */}
            <Button
              variant="primary"
              size="lg"
              className="flex-1"
              onClick={handleAddToCart}
              disabled={isAdding || cartLoading}
            >
              {isAdding ? 'Adding...' : 'Add to Cart'}
            </Button>
          </div>
        )}

        {/* Inquire Button */}
        {requiresInquiry && (
          <div className="space-y-3">
            <p className="text-sm text-slate-400">
              This item requires a personalized inquiry. Contact us to discuss availability and pricing.
            </p>
            <Button variant="secondary" size="lg" className="w-full">
              Inquire About This Item
            </Button>
          </div>
        )}

        {/* Out of Stock */}
        {!inStock && !requiresInquiry && (
          <Button variant="ghost" size="lg" className="w-full" disabled>
            Out of Stock
          </Button>
        )}

        {/* Product Details Tabs */}
        {visibleTabs.length > 0 && (
          <div className="border-t border-slate-700 pt-6 mt-8">
            {/* Tab Headers */}
            <div className="flex gap-6 border-b border-slate-700">
              {visibleTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`pb-3 text-sm font-medium transition-colors relative ${
                    activeTab === tab.id
                      ? 'text-gold-400'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                  {activeTab === tab.id && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-gold-500" />
                  )}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="pt-4">
              {activeTab === 'details' && (
                <div
                  className="prose prose-invert prose-slate max-w-none"
                  dangerouslySetInnerHTML={{ __html: product.description }}
                />
              )}
              {activeTab === 'provenance' && product.provenance_info && (
                <div className="text-slate-300 whitespace-pre-wrap">
                  {product.provenance_info}
                </div>
              )}
              {activeTab === 'authentication' && product.authentication_docs && (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400">
                    This item includes the following authentication documents:
                  </p>
                  <ul className="space-y-2">
                    {product.authentication_docs.map((doc, index) => (
                      <li key={index} className="flex items-center gap-2 text-slate-300">
                        <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {doc}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* SKU */}
        {product.sku && (
          <p className="text-xs text-slate-500">
            SKU: {selectedVariant?.sku || product.sku}
          </p>
        )}
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <ShareToChat
          product={product}
          onClose={() => setShowShareModal(false)}
        />
      )}
    </div>
  );
}
