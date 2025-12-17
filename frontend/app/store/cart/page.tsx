'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useCart } from '@/contexts/CartContext';
import { Button } from '@/components/ui/Button';

export default function CartPage() {
  const {
    items,
    subtotalDollars,
    hasPhysicalItems,
    hasDigitalItems,
    isLoading,
    updateQuantity,
    removeItem,
    clearCart,
  } = useCart();

  if (items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto text-center py-16">
        <div className="text-6xl mb-4">🛒</div>
        <h1 className="text-3xl font-bold text-slate-100 mb-4">Your Cart is Empty</h1>
        <p className="text-slate-400 mb-8">
          Looks like you haven't added anything to your cart yet.
        </p>
        <Link href="/store">
          <Button variant="primary" size="lg">
            Browse Store
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-slate-100">Shopping Cart</h1>
        <button
          onClick={() => clearCart()}
          className="text-sm text-slate-400 hover:text-red-400 transition-colors"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="glass rounded-xl p-4 flex gap-4"
            >
              {/* Product Image */}
              <Link
                href={`/store/product/${item.product.slug}`}
                className="relative w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-slate-800"
              >
                {item.product.primary_image ? (
                  <Image
                    src={item.product.primary_image.image_url}
                    alt={item.product.name}
                    fill
                    className="object-cover"
                    sizes="96px"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-600">
                    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
              </Link>

              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <Link
                  href={`/store/product/${item.product.slug}`}
                  className="font-medium text-slate-100 hover:text-gold-400 transition-colors line-clamp-2"
                >
                  {item.product.name}
                </Link>

                {item.variant && (
                  <p className="text-sm text-slate-400 mt-1">{item.variant.name}</p>
                )}

                <p className="text-sm text-slate-500 mt-1">
                  ${(item.unit_price_cents / 100).toFixed(2)} each
                </p>

                {/* Quantity Controls */}
                <div className="flex items-center gap-3 mt-3">
                  <div className="flex items-center border border-slate-600 rounded-lg">
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      disabled={isLoading}
                      className="px-3 py-1.5 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                      </svg>
                    </button>
                    <span className="px-3 text-slate-200 font-medium min-w-[2.5rem] text-center">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      disabled={isLoading}
                      className="px-3 py-1.5 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                    </button>
                  </div>

                  <button
                    onClick={() => removeItem(item.id)}
                    disabled={isLoading}
                    className="text-sm text-slate-500 hover:text-red-400 transition-colors disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              </div>

              {/* Line Total */}
              <div className="text-right">
                <p className="font-bold text-gold-400">
                  ${item.line_total_dollars.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="glass rounded-xl p-6 sticky top-4">
            <h2 className="text-xl font-semibold text-slate-100 mb-4">Order Summary</h2>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between">
                <span className="text-slate-400">Subtotal ({items.length} items)</span>
                <span className="text-slate-200">${subtotalDollars.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Shipping</span>
                <span className="text-slate-400">Calculated at checkout</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tax</span>
                <span className="text-slate-400">Calculated at checkout</span>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-4 mb-6">
              <div className="flex justify-between text-lg font-bold">
                <span className="text-slate-100">Estimated Total</span>
                <span className="text-gold-400">${subtotalDollars.toFixed(2)}</span>
              </div>
            </div>

            <Link href="/store/checkout">
              <Button variant="primary" size="lg" className="w-full">
                Proceed to Checkout
              </Button>
            </Link>

            <Link
              href="/store"
              className="block text-center text-sm text-slate-400 hover:text-gold-400 transition-colors mt-4"
            >
              Continue Shopping
            </Link>

            {/* Cart Type Info */}
            <div className="mt-6 pt-4 border-t border-slate-700 text-xs text-slate-500 space-y-1">
              {hasPhysicalItems && (
                <p className="flex items-center gap-1">
                  <span>📦</span> Includes physical items (shipping required)
                </p>
              )}
              {hasDigitalItems && (
                <p className="flex items-center gap-1">
                  <span>⬇️</span> Includes digital downloads
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
