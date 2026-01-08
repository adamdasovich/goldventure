'use client';

import { AuthProvider } from '@/contexts/AuthContext';
import { CartProvider } from '@/contexts/CartContext';
import { IdleTimeoutProvider } from '@/contexts/IdleTimeoutContext';
import { CartSidebar } from '@/components/store';
import CanonicalUrl from '@/components/CanonicalUrl';
import IdleWarningModal from '@/components/auth/IdleWarningModal';

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <IdleTimeoutProvider>
        <CartProvider>
          <CanonicalUrl />
          {children}
          <CartSidebar />
          <IdleWarningModal />
        </CartProvider>
      </IdleTimeoutProvider>
    </AuthProvider>
  );
}
