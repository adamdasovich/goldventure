'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { storeAPI } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import type { StoreOrder } from '@/types/api';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  paid: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
  processing: 'bg-purple-500/20 text-purple-400 border-purple-500/40',
  shipped: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
  delivered: 'bg-green-500/20 text-green-400 border-green-500/40',
  refunded: 'bg-red-500/20 text-red-400 border-red-500/40',
  cancelled: 'bg-slate-500/20 text-slate-400 border-slate-500/40',
};

const statusLabels: Record<string, string> = {
  pending: 'Pending',
  paid: 'Paid',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  refunded: 'Refunded',
  cancelled: 'Cancelled',
};

export default function OrdersPage() {
  const router = useRouter();
  const { accessToken, isAuthenticated, isLoading: authLoading } = useAuth();
  const [orders, setOrders] = useState<StoreOrder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/account/orders');
      return;
    }

    const fetchOrders = async () => {
      try {
        setIsLoading(true);
        const response = await storeAPI.orders.getAll(accessToken!);
        setOrders(response.results || []);
      } catch (err) {
        console.error('Failed to fetch orders:', err);
        setError('Failed to load orders');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrders();
  }, [accessToken, isAuthenticated, authLoading, router]);

  if (authLoading || (!isAuthenticated && !authLoading)) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-bold text-slate-100 mb-8">My Orders</h1>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="glass rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-slate-800 rounded w-1/4 mb-4" />
              <div className="h-4 bg-slate-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <div className="mb-4 flex justify-center">
          <svg className="w-16 h-16 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-slate-100 mb-4">No Orders Yet</h1>
        <p className="text-slate-400 mb-8">
          You haven't placed any orders yet. Start shopping to see your orders here.
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
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-slate-100 mb-8">My Orders</h1>

      <div className="space-y-6">
        {orders.map((order) => (
          <div key={order.id} className="glass rounded-xl overflow-hidden">
            {/* Order Header */}
            <div className="bg-slate-800/50 px-6 py-4 border-b border-slate-700">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Order placed</p>
                    <p className="text-slate-200 font-medium">
                      {new Date(order.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                  <div className="hidden sm:block w-px h-10 bg-slate-700" />
                  <div className="hidden sm:block">
                    <p className="text-sm text-slate-400">Order #</p>
                    <p className="text-slate-200 font-medium">{order.id}</p>
                  </div>
                </div>
                <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${statusColors[order.status] || statusColors.pending}`}>
                  {statusLabels[order.status] || order.status}
                </span>
              </div>
            </div>

            {/* Order Items */}
            <div className="p-6">
              <div className="space-y-4">
                {order.items?.map((item) => (
                  <div key={item.id} className="flex items-start gap-4 pb-4 border-b border-slate-700/50 last:border-0 last:pb-0">
                    {/* Item Icon */}
                    <div className="w-12 h-12 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-6 h-6 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                    </div>
                    {/* Item Details */}
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-100 font-medium truncate">
                        {item.product_name}
                        {item.variant_name && (
                          <span className="text-slate-400 font-normal"> - {item.variant_name}</span>
                        )}
                      </p>
                      <p className="text-sm text-slate-400 mt-0.5">
                        Qty: {item.quantity} × ${item.price_dollars.toFixed(2)}
                      </p>
                      {/* Digital Download Link */}
                      {item.digital_download_url && (
                        <a
                          href={item.digital_download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-sm text-gold-400 hover:text-gold-300 mt-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download
                        </a>
                      )}
                    </div>
                    {/* Item Total */}
                    <div className="text-right flex-shrink-0">
                      <p className="text-slate-100 font-medium">
                        ${item.line_total_dollars.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Order Summary */}
              <div className="mt-6 pt-4 border-t border-slate-700">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-slate-400">
                    <span>Subtotal</span>
                    <span>${order.subtotal_dollars.toFixed(2)}</span>
                  </div>
                  {order.shipping_dollars > 0 && (
                    <div className="flex justify-between text-slate-400">
                      <span>Shipping{order.shipping_rate_name && ` (${order.shipping_rate_name})`}</span>
                      <span>${order.shipping_dollars.toFixed(2)}</span>
                    </div>
                  )}
                  {order.tax_dollars > 0 && (
                    <div className="flex justify-between text-slate-400">
                      <span>Tax</span>
                      <span>${order.tax_dollars.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-lg font-semibold pt-2 border-t border-slate-700">
                    <span className="text-slate-200">Total</span>
                    <span className="text-gold-400">${order.total_dollars.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Shipping Address */}
              {order.shipping_address && order.shipping_address.line1 && (
                <div className="mt-6 pt-4 border-t border-slate-700">
                  <p className="text-sm font-medium text-slate-300 mb-2">Shipping Address</p>
                  <div className="text-sm text-slate-400">
                    <p>{order.shipping_address.name}</p>
                    <p>{order.shipping_address.line1}</p>
                    {order.shipping_address.line2 && <p>{order.shipping_address.line2}</p>}
                    <p>
                      {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}
                    </p>
                    <p>{order.shipping_address.country}</p>
                  </div>
                </div>
              )}

              {/* Tracking Info */}
              {order.tracking_number && (
                <div className="mt-6 pt-4 border-t border-slate-700">
                  <p className="text-sm font-medium text-slate-300 mb-2">Tracking</p>
                  <p className="text-sm text-slate-200 font-mono bg-slate-800 px-3 py-2 rounded inline-block">
                    {order.tracking_number}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
