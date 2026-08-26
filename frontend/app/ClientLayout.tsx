"use client";

import { AuthProvider } from "@/contexts/AuthContext";
import { CartProvider } from "@/contexts/CartContext";
import { IdleTimeoutProvider } from "@/contexts/IdleTimeoutContext";
import { CartSidebar } from "@/components/store";
import IdleWarningModal from "@/components/auth/IdleWarningModal";
import { AssistantProvider } from "@/contexts/AssistantContext";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <IdleTimeoutProvider>
        <CartProvider>
          <AssistantProvider>
            {children}
            <CartSidebar />
            <IdleWarningModal />
          </AssistantProvider>
        </CartProvider>
      </IdleTimeoutProvider>
    </AuthProvider>
  );
}
