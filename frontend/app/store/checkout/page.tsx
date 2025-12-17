'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { storeAPI } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { StoreShippingRate, ShippingAddress } from '@/types/api';

export default function CheckoutPage() {
  const router = useRouter();
  const { items, subtotalDollars, hasPhysicalItems, hasDigitalItems, refreshCart } = useCart();
  const { accessToken, isAuthenticated, user } = useAuth();

  const [shippingRates, setShippingRates] = useState<StoreShippingRate[]>([]);
  const [selectedRateId, setSelectedRateId] = useState<number | null>(null);
  const [isLoadingRates, setIsLoadingRates] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [shippingAddress, setShippingAddress] = useState<ShippingAddress>({
    name: user?.full_name || '',
    line1: '',
    line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
  });

  // Fetch shipping rates when country changes
  useEffect(() => {
    const fetchRates = async () => {
      if (!hasPhysicalItems) return;

      setIsLoadingRates(true);
      try {
        const response = await storeAPI.shipping.calculate(
          accessToken || undefined,
          shippingAddress.country
        );
        setShippingRates(response.rates);
        if (response.rates.length > 0 && !selectedRateId) {
          setSelectedRateId(response.rates[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch shipping rates:', err);
      } finally {
        setIsLoadingRates(false);
      }
    };

    fetchRates();
  }, [shippingAddress.country, hasPhysicalItems, accessToken]);

  const selectedRate = shippingRates.find((r) => r.id === selectedRateId);
  const shippingCost = selectedRate?.price_dollars || 0;
  const totalDollars = subtotalDollars + shippingCost;

  const handleInputChange = (field: keyof ShippingAddress, value: string) => {
    setShippingAddress((prev) => ({ ...prev, [field]: value }));
  };

  const handleCheckout = async () => {
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/store/checkout');
      return;
    }

    if (hasPhysicalItems && !selectedRateId) {
      setError('Please select a shipping method');
      return;
    }

    if (hasPhysicalItems) {
      // Validate shipping address
      if (!shippingAddress.name || !shippingAddress.line1 || !shippingAddress.city ||
          !shippingAddress.state || !shippingAddress.postal_code) {
        setError('Please fill in all required shipping fields');
        return;
      }
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await storeAPI.checkout(accessToken!, {
        shipping_address: hasPhysicalItems ? shippingAddress : undefined,
        shipping_rate_id: hasPhysicalItems ? selectedRateId! : undefined,
        success_url: `${window.location.origin}/store/checkout/success`,
        cancel_url: `${window.location.origin}/store/checkout/cancel`,
      });

      // Redirect to Stripe Checkout
      window.location.href = response.checkout_url;
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.message || 'Failed to process checkout');
      setIsProcessing(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="mb-4 flex justify-center">
          <svg className="w-16 h-16 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Your Cart is Empty</h1>
        <p className="text-slate-400 mb-6">
          Add some items to your cart before checking out.
        </p>
        <Link href="/store">
          <Button variant="primary">Browse Store</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-100 mb-8">Checkout</h1>

      <div className="grid lg:grid-cols-5 gap-8">
        {/* Left: Form */}
        <div className="lg:col-span-3 space-y-6">
          {/* Shipping Address (for physical items) */}
          {hasPhysicalItems && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-xl font-semibold text-slate-100 mb-4">Shipping Address</h2>

              <div className="space-y-4">
                <Input
                  label="Full Name"
                  value={shippingAddress.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  required
                />

                <Input
                  label="Address Line 1"
                  value={shippingAddress.line1}
                  onChange={(e) => handleInputChange('line1', e.target.value)}
                  placeholder="Street address"
                  required
                />

                <Input
                  label="Address Line 2"
                  value={shippingAddress.line2 || ''}
                  onChange={(e) => handleInputChange('line2', e.target.value)}
                  placeholder="Apartment, suite, etc. (optional)"
                />

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="City"
                    value={shippingAddress.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    required
                  />
                  <Input
                    label="State/Province"
                    value={shippingAddress.state}
                    onChange={(e) => handleInputChange('state', e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Postal Code"
                    value={shippingAddress.postal_code}
                    onChange={(e) => handleInputChange('postal_code', e.target.value)}
                    required
                  />
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Country
                    </label>
                    <select
                      value={shippingAddress.country}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
                    >
                      <option value="US">United States</option>
                      <option value="CA">Canada</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Shipping Method */}
          {hasPhysicalItems && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-xl font-semibold text-slate-100 mb-4">Shipping Method</h2>

              {isLoadingRates ? (
                <div className="animate-pulse space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-16 bg-slate-800 rounded-lg" />
                  ))}
                </div>
              ) : shippingRates.length > 0 ? (
                <div className="space-y-3">
                  {shippingRates.map((rate) => (
                    <label
                      key={rate.id}
                      className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedRateId === rate.id
                          ? 'border-gold-500 bg-gold-500/10'
                          : 'border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="radio"
                          name="shipping"
                          checked={selectedRateId === rate.id}
                          onChange={() => setSelectedRateId(rate.id)}
                          className="text-gold-500 focus:ring-gold-500"
                        />
                        <div>
                          <p className="font-medium text-slate-100">{rate.name}</p>
                          <p className="text-sm text-slate-400">{rate.delivery_estimate}</p>
                        </div>
                      </div>
                      <span className="font-medium text-gold-400">
                        ${rate.price_dollars.toFixed(2)}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400">
                  No shipping options available for your location.
                </p>
              )}
            </div>
          )}

          {/* Digital Only Notice */}
          {hasDigitalItems && !hasPhysicalItems && (
            <div className="glass rounded-xl p-6 border border-blue-500/20 bg-gradient-to-r from-blue-900/20 to-slate-900">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-slate-100 mb-2">Digital Download</h2>
                  <p className="text-slate-400">
                    Your cart contains only digital items. Download links will be sent to your email address immediately after purchase.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Order Summary */}
        <div className="lg:col-span-2">
          <div className="glass rounded-xl p-6 sticky top-4">
            <h2 className="text-xl font-semibold text-slate-100 mb-4">Order Summary</h2>

            {/* Items */}
            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
              {items.map((item) => (
                <div key={item.id} className="flex gap-3">
                  <div className="relative w-16 h-16 flex-shrink-0 rounded bg-slate-800 overflow-hidden">
                    {item.product.primary_image ? (
                      <Image
                        src={item.product.primary_image.image_url}
                        alt={item.product.name}
                        fill
                        className="object-cover"
                        sizes="64px"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-600">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-100 truncate">
                      {item.product.name}
                    </p>
                    {item.variant && (
                      <p className="text-xs text-slate-400">{item.variant.name}</p>
                    )}
                    <p className="text-xs text-slate-400">Qty: {item.quantity}</p>
                  </div>
                  <span className="text-sm font-medium text-slate-200">
                    ${item.line_total_dollars.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-700 pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Subtotal</span>
                <span className="text-slate-200">${subtotalDollars.toFixed(2)}</span>
              </div>
              {hasPhysicalItems && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Shipping</span>
                  <span className="text-slate-200">
                    {selectedRate ? `$${shippingCost.toFixed(2)}` : '-'}
                  </span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Tax</span>
                <span className="text-slate-400">Calculated at checkout</span>
              </div>
              <div className="flex justify-between text-lg font-bold pt-2 border-t border-slate-700">
                <span className="text-slate-100">Total</span>
                <span className="text-gold-400">${totalDollars.toFixed(2)}</span>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-sm text-red-400">
                {error}
              </div>
            )}

            <Button
              variant="primary"
              size="lg"
              className="w-full mt-6"
              onClick={handleCheckout}
              disabled={isProcessing || (hasPhysicalItems && !selectedRateId)}
            >
              {isProcessing ? 'Processing...' : isAuthenticated ? 'Proceed to Payment' : 'Login to Checkout'}
            </Button>

            <p className="text-xs text-slate-500 text-center mt-4">
              Secure checkout powered by Stripe
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
