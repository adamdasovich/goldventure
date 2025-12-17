'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function CheckoutCancelPage() {
  return (
    <div className="max-w-2xl mx-auto text-center py-12">
      {/* Cancel Icon */}
      <div className="inline-block mb-8">
        <div className="w-24 h-24 rounded-full bg-slate-700/50 flex items-center justify-center">
          <svg
            className="w-12 h-12 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>
      </div>

      <h1 className="text-3xl font-bold text-slate-100 mb-4">
        Checkout Cancelled
      </h1>

      <p className="text-lg text-slate-400 mb-8">
        Your payment was cancelled. No charges were made. Your cart items are still saved.
      </p>

      {/* Info Box */}
      <div className="glass rounded-xl p-6 mb-8 text-left">
        <h2 className="text-lg font-semibold text-slate-100 mb-3">Need Help?</h2>
        <p className="text-slate-400 mb-4">
          If you experienced any issues during checkout or have questions about your order,
          our support team is here to help.
        </p>
        <ul className="text-sm text-slate-400 space-y-2">
          <li className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Your cart items have been preserved
          </li>
          <li className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            No payment was processed
          </li>
          <li className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            You can try again at any time
          </li>
        </ul>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link href="/store/checkout">
          <Button variant="primary" size="lg">
            Return to Checkout
          </Button>
        </Link>
        <Link href="/store">
          <Button variant="secondary" size="lg">
            Continue Shopping
          </Button>
        </Link>
      </div>
    </div>
  );
}
