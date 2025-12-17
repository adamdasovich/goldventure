'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { storeAdminAPI, type StoreOrderStats } from '@/lib/api';

export default function StoreAdminDashboard() {
  const { accessToken } = useAuth();
  const [stats, setStats] = useState<StoreOrderStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;

    const fetchStats = async () => {
      try {
        const data = await storeAdminAPI.orders.getStats(accessToken);
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [accessToken]);

  const statCards = [
    {
      label: 'Total Revenue',
      value: stats ? `$${stats.total_revenue_dollars.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '-',
      icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Total Orders',
      value: stats?.total_orders?.toString() || '0',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Pending Orders',
      value: stats?.pending_orders?.toString() || '0',
      icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
    },
    {
      label: 'Last 30 Days',
      value: stats ? `$${stats.last_30_days_revenue_dollars.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '-',
      icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
  ];

  const quickActions = [
    {
      label: 'Add New Product',
      href: '/admin/store/products/new',
      icon: 'M12 4v16m8-8H4',
      color: 'bg-gold-500 hover:bg-gold-600 text-slate-900',
    },
    {
      label: 'View Products',
      href: '/admin/store/products',
      icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
      color: 'bg-slate-700 hover:bg-slate-600 text-slate-100',
    },
    {
      label: 'Manage Orders',
      href: '/admin/store/orders',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      color: 'bg-slate-700 hover:bg-slate-600 text-slate-100',
    },
    {
      label: 'Categories',
      href: '/admin/store/categories',
      icon: 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z',
      color: 'bg-slate-700 hover:bg-slate-600 text-slate-100',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Store Dashboard</h1>
        <p className="text-slate-400 mt-1">Manage your products, orders, and store settings</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="glass rounded-xl p-5">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                <svg className={`w-6 h-6 ${stat.color}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={stat.icon} />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                {isLoading ? (
                  <div className="h-7 w-20 bg-slate-700 rounded animate-pulse mt-1" />
                ) : (
                  <p className="text-xl font-bold text-slate-100">{stat.value}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.label}
              href={action.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${action.color}`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={action.icon} />
              </svg>
              {action.label}
            </Link>
          ))}
        </div>
      </div>

      {/* Order Status Overview */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Order Status Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Pending', count: stats?.pending_orders || 0, color: 'bg-yellow-500' },
            { label: 'Processing', count: stats?.processing_orders || 0, color: 'bg-blue-500' },
            { label: 'Shipped', count: stats?.shipped_orders || 0, color: 'bg-cyan-500' },
            { label: 'Delivered', count: stats?.delivered_orders || 0, color: 'bg-green-500' },
            { label: 'Last 30 Days', count: stats?.last_30_days_orders || 0, color: 'bg-purple-500' },
          ].map((status) => (
            <div key={status.label} className="text-center">
              <div className={`w-12 h-12 rounded-full ${status.color}/20 flex items-center justify-center mx-auto mb-2`}>
                {isLoading ? (
                  <div className="w-6 h-6 bg-slate-700 rounded animate-pulse" />
                ) : (
                  <span className={`text-lg font-bold ${status.color.replace('bg-', 'text-')}`}>
                    {status.count}
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-400">{status.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Placeholder */}
      <div className="glass rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100">Recent Orders</h2>
          <Link
            href="/admin/store/orders"
            className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
          >
            View All
          </Link>
        </div>
        <p className="text-slate-400 text-sm">
          View and manage recent orders from the orders page.
        </p>
      </div>
    </div>
  );
}
