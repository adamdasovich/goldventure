'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CartButton } from './CartButton';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

const storeNavItems = [
  { href: '/store', label: 'All Products' },
  { href: '/store/vault', label: 'The Vault' },
  { href: '/store/field-gear', label: 'Field Gear' },
  { href: '/store/resource-library', label: 'Resource Library' },
];

export function StoreHeader() {
  const pathname = usePathname();
  const { user } = useAuth();

  // Check if user is admin (staff or superuser)
  const isAdmin = user?.is_staff || user?.is_superuser;

  return (
    <header className="glass-nav sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Back to Main Site + Logo */}
          <div className="flex items-center gap-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-400 hover:text-gold-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="text-sm hidden sm:inline">Back to Site</span>
            </Link>

            <Link href="/store" className="flex items-center gap-2">
              <span className="text-xl font-bold text-gold-400">GV</span>
              <span className="text-xl font-semibold text-slate-100">Store</span>
            </Link>
          </div>

          {/* Center: Store Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {storeNavItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== '/store' && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gold-500/20 text-gold-400'
                      : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/50'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: Admin + Cart + Account */}
          <div className="flex items-center gap-3">
            {/* Admin Button - Only visible to staff/superusers */}
            {isAdmin && (
              <Link href="/admin/store">
                <Button
                  variant="ghost"
                  size="sm"
                  className="hidden sm:inline-flex items-center gap-1.5 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Admin
                </Button>
              </Link>
            )}
            <Link href="/store/cart">
              <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
                View Cart
              </Button>
            </Link>
            <CartButton />
          </div>
        </div>

        {/* Mobile Navigation */}
        <nav className="md:hidden flex items-center gap-2 pb-3 overflow-x-auto">
          {storeNavItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== '/store' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-gold-500/20 text-gold-400'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-800/50'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          {/* Admin link on mobile */}
          {isAdmin && (
            <Link
              href="/admin/store"
              className="px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors bg-amber-500/20 text-amber-400"
            >
              Admin
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
