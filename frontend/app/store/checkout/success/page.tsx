'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useCart } from '@/contexts/CartContext';
import { Button } from '@/components/ui/Button';

function CheckoutSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const { refreshCart } = useCart();

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Refresh cart to clear it after successful purchase
    refreshCart().catch(console.error).finally(() => setIsLoading(false));
  }, [refreshCart]);

  return (
    <div className="max-w-2xl mx-auto text-center py-12">
      {/* Success Animation */}
      <div className="relative inline-block mb-8">
        <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center animate-pulse">
          <svg
            className="w-12 h-12 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <div className="absolute inset-0 w-24 h-24 rounded-full border-2 border-green-500 animate-ping opacity-20" />
      </div>

      <h1 className="text-3xl font-bold text-slate-100 mb-4">
        Thank You for Your Order!
      </h1>

      <p className="text-lg text-slate-400 mb-8">
        Your payment was successful. We've sent a confirmation email with your order details.
      </p>

      {/* Order Info */}
      <div className="glass rounded-xl p-6 mb-8 text-left">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">What's Next?</h2>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-gold-400 font-bold">1</span>
            </div>
            <div>
              <p className="font-medium text-slate-100">Check Your Email</p>
              <p className="text-sm text-slate-400">
                You'll receive an order confirmation with receipt and tracking information.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-gold-400 font-bold">2</span>
            </div>
            <div>
              <p className="font-medium text-slate-100">Digital Downloads</p>
              <p className="text-sm text-slate-400">
                If your order includes digital items, download links are available in the email.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-gold-400 font-bold">3</span>
            </div>
            <div>
              <p className="font-medium text-slate-100">Physical Shipping</p>
              <p className="text-sm text-slate-400">
                Physical items will ship within 1-2 business days with tracking.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Button type="button" variant="primary" size="lg" onClick={() => router.push('/store')}>
          Continue Shopping
        </Button>
        <Button type="button" variant="secondary" size="lg" onClick={() => router.push('/account/orders')}>
          View My Orders
        </Button>
      </div>

      {/* Session ID for reference */}
      {sessionId && (
        <p className="text-xs text-slate-500 mt-8">
          Reference: {sessionId.slice(0, 20)}...
        </p>
      )}
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="animate-pulse">
          <div className="w-24 h-24 rounded-full bg-slate-700 mx-auto mb-8" />
          <div className="h-8 bg-slate-700 rounded w-64 mx-auto mb-4" />
          <div className="h-4 bg-slate-700 rounded w-96 mx-auto" />
        </div>
      </div>
    }>
      <CheckoutSuccessContent />
    </Suspense>
  );
}
