'use client';

import { AuthProvider } from '@/contexts/AuthContext';
import { CartProvider } from '@/contexts/CartContext';
import { CartSidebar } from '@/components/store';
import CanonicalUrl from '@/components/CanonicalUrl';

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <CartProvider>
        <CanonicalUrl />
        {children}
        <CartSidebar />
      </CartProvider>
    </AuthProvider>
  );
}
