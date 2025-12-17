'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { storeAdminAPI, type StoreOrderAdmin } from '@/lib/api';
import { Button } from '@/components/ui/Button';

const ORDER_STATUSES = [
  { value: 'paid', label: 'Paid', color: 'bg-blue-500/20 text-blue-400 border-blue-500/40' },
  { value: 'processing', label: 'Processing', color: 'bg-purple-500/20 text-purple-400 border-purple-500/40' },
  { value: 'shipped', label: 'Shipped', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40' },
  { value: 'delivered', label: 'Delivered', color: 'bg-green-500/20 text-green-400 border-green-500/40' },
  { value: 'refunded', label: 'Refunded', color: 'bg-red-500/20 text-red-400 border-red-500/40' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-slate-500/20 text-slate-400 border-slate-500/40' },
];

export default function OrdersPage() {
  const { accessToken } = useAuth();
  const [orders, setOrders] = useState<StoreOrderAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<StoreOrderAdmin | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchOrders = useCallback(async () => {
    if (!accessToken) return;

    setIsLoading(true);
    try {
      const params: { status?: string; search?: string } = {};
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;

      const data = await storeAdminAPI.orders.getAll(accessToken, params);
      setOrders(data);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, statusFilter, search]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleUpdateStatus = async (orderId: number, newStatus: string) => {
    if (!accessToken) return;

    try {
      const updated = await storeAdminAPI.orders.update(accessToken, orderId, {
        status: newStatus,
      });
      setOrders(orders.map(o => o.id === orderId ? updated : o));
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(updated);
      }
    } catch (err) {
      console.error('Failed to update order:', err);
      alert('Failed to update order status');
    }
  };

  const handleUpdateTracking = async (orderId: number, trackingNumber: string) => {
    if (!accessToken) return;

    try {
      const updated = await storeAdminAPI.orders.update(accessToken, orderId, {
        tracking_number: trackingNumber,
      });
      setOrders(orders.map(o => o.id === orderId ? updated : o));
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(updated);
      }
    } catch (err) {
      console.error('Failed to update tracking:', err);
      alert('Failed to update tracking number');
    }
  };

  const getStatusColor = (status: string) => {
    return ORDER_STATUSES.find(s => s.value === status)?.color || ORDER_STATUSES[0].color;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Orders</h1>
        <p className="text-slate-400 mt-1">Manage customer orders and fulfillment</p>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative md:col-span-2">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by email, order ID, or tracking..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
          >
            <option value="">All Statuses</option>
            {ORDER_STATUSES.map((status) => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="glass rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : orders.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="w-16 h-16 text-slate-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="text-lg font-medium text-slate-100 mb-2">No orders found</h3>
            <p className="text-slate-400">Orders will appear here once customers make purchases.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Order</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Customer</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Total</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Date</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <span className="font-medium text-slate-100">#{order.id}</span>
                    <p className="text-sm text-slate-400">{order.items.length} item(s)</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-slate-100">{order.customer_email}</p>
                    {order.user_name && (
                      <p className="text-sm text-slate-400">{order.user_name}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-gold-400 font-medium">
                      ${order.total_dollars.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(order.status)}`}>
                      {ORDER_STATUSES.find(s => s.value === order.status)?.label || order.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-sm">
                    {new Date(order.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-gold-400 hover:text-gold-300 text-sm font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
          <div className="glass rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-slate-800 px-6 py-4 border-b border-slate-700 flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-100">Order #{selectedOrder.id}</h2>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-2 text-slate-400 hover:text-slate-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Customer Info */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Customer</h3>
                <p className="text-slate-100">{selectedOrder.customer_email}</p>
                {selectedOrder.user_name && (
                  <p className="text-slate-400">{selectedOrder.user_name}</p>
                )}
              </div>

              {/* Order Items */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Items</h3>
                <div className="space-y-2">
                  {selectedOrder.items.map((item) => (
                    <div key={item.id} className="flex justify-between items-center bg-slate-800/50 rounded-lg px-4 py-3">
                      <div>
                        <p className="text-slate-100">{item.product_name}</p>
                        {item.variant_name && (
                          <p className="text-sm text-slate-400">{item.variant_name}</p>
                        )}
                        <p className="text-sm text-slate-400">Qty: {item.quantity}</p>
                      </div>
                      <span className="text-slate-100">${item.price_dollars.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Order Summary */}
              <div className="border-t border-slate-700 pt-4 space-y-2">
                <div className="flex justify-between text-slate-400">
                  <span>Subtotal</span>
                  <span>${selectedOrder.subtotal_dollars.toFixed(2)}</span>
                </div>
                {selectedOrder.shipping_dollars > 0 && (
                  <div className="flex justify-between text-slate-400">
                    <span>Shipping</span>
                    <span>${selectedOrder.shipping_dollars.toFixed(2)}</span>
                  </div>
                )}
                {selectedOrder.tax_dollars > 0 && (
                  <div className="flex justify-between text-slate-400">
                    <span>Tax</span>
                    <span>${selectedOrder.tax_dollars.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-semibold pt-2 border-t border-slate-700">
                  <span className="text-slate-100">Total</span>
                  <span className="text-gold-400">${selectedOrder.total_dollars.toFixed(2)}</span>
                </div>
              </div>

              {/* Shipping Address */}
              {selectedOrder.shipping_address && selectedOrder.shipping_address.line1 && (
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Shipping Address</h3>
                  <div className="text-slate-300 text-sm">
                    <p>{selectedOrder.shipping_address.name}</p>
                    <p>{selectedOrder.shipping_address.line1}</p>
                    {selectedOrder.shipping_address.line2 && <p>{selectedOrder.shipping_address.line2}</p>}
                    <p>{selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}</p>
                    <p>{selectedOrder.shipping_address.country}</p>
                  </div>
                </div>
              )}

              {/* Status Update */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Update Status</h3>
                <div className="flex flex-wrap gap-2">
                  {ORDER_STATUSES.map((status) => (
                    <button
                      key={status.value}
                      onClick={() => handleUpdateStatus(selectedOrder.id, status.value)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                        selectedOrder.status === status.value
                          ? status.color
                          : 'bg-slate-700 text-slate-400 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      {status.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tracking Number */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Tracking Number</h3>
                <div className="flex gap-2">
                  <input
                    type="text"
                    defaultValue={selectedOrder.tracking_number || ''}
                    placeholder="Enter tracking number"
                    className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                    onBlur={(e) => {
                      if (e.target.value !== selectedOrder.tracking_number) {
                        handleUpdateTracking(selectedOrder.id, e.target.value);
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.currentTarget.blur();
                      }
                    }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Press Enter or click outside to save. Setting status to &quot;Shipped&quot; will send a notification email.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
