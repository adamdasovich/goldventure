'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CartButton } from './CartButton';
import { Button } from '@/components/ui/Button';

const storeNavItems = [
  { href: '/store', label: 'All Products' },
  { href: '/store/vault', label: 'The Vault' },
  { href: '/store/field-gear', label: 'Field Gear' },
  { href: '/store/resource-library', label: 'Resource Library' },
];

export function StoreHeader() {
  const pathname = usePathname();

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

          {/* Right: Cart + Account */}
          <div className="flex items-center gap-4">
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
        </nav>
      </div>
    </header>
  );
}
