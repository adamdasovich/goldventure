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

      <div className="space-y-4">
        {orders.map((order) => (
          <div key={order.id} className="glass rounded-xl p-6">
            <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
              <div>
                <p className="text-sm text-slate-400">
                  Order #{order.id} &bull; {new Date(order.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
                <p className="text-lg font-semibold text-gold-400 mt-1">
                  ${order.total_dollars.toFixed(2)}
                </p>
              </div>
              <span className={`px-3 py-1 text-xs font-medium rounded-full border ${statusColors[order.status] || statusColors.pending}`}>
                {statusLabels[order.status] || order.status}
              </span>
            </div>

            {/* Order Items Summary */}
            <div className="border-t border-slate-700 pt-4">
              <p className="text-sm text-slate-400 mb-2">
                {order.items?.length || 0} item{(order.items?.length || 0) !== 1 ? 's' : ''}
              </p>
              <div className="flex flex-wrap gap-2">
                {order.items?.slice(0, 3).map((item) => (
                  <span key={item.id} className="text-sm text-slate-300">
                    {item.product_name} x{item.quantity}
                  </span>
                ))}
                {(order.items?.length || 0) > 3 && (
                  <span className="text-sm text-slate-500">
                    +{(order.items?.length || 0) - 3} more
                  </span>
                )}
              </div>
            </div>

            {/* Tracking Info */}
            {order.tracking_number && (
              <div className="border-t border-slate-700 pt-4 mt-4">
                <p className="text-sm text-slate-400">
                  Tracking: <span className="text-slate-200">{order.tracking_number}</span>
                </p>
              </div>
            )}

            {/* Digital Downloads */}
            {order.items?.some(item => item.digital_download_url) && (
              <div className="border-t border-slate-700 pt-4 mt-4">
                <p className="text-sm font-medium text-slate-300 mb-2">Digital Downloads</p>
                <div className="space-y-2">
                  {order.items?.filter(item => item.digital_download_url).map((item) => (
                    <a
                      key={item.id}
                      href={item.digital_download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-sm text-gold-400 hover:text-gold-300"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Download {item.product_name}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
