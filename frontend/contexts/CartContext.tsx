'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { storeAPI } from '@/lib/api';
import type { StoreCart, StoreCartItem, StoreProductList } from '@/types/api';

interface CartContextType {
  cart: StoreCart | null;
  items: StoreCartItem[];
  itemCount: number;
  subtotal: number;
  subtotalDollars: number;
  hasPhysicalItems: boolean;
  hasDigitalItems: boolean;
  isLoading: boolean;
  isOpen: boolean;
  error: string | null;

  // Actions
  addItem: (productId: number, variantId?: number, quantity?: number) => Promise<void>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

// Local storage key for guest cart
const GUEST_CART_KEY = 'gv_guest_cart';

interface GuestCartItem {
  productId: number;
  variantId?: number;
  quantity: number;
}

export function CartProvider({ children }: { children: ReactNode }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [cart, setCart] = useState<StoreCart | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Computed values
  const items = cart?.items || [];
  const itemCount = cart?.item_count || 0;
  const subtotal = cart?.subtotal_cents || 0;
  const subtotalDollars = cart?.subtotal_dollars || 0;
  const hasPhysicalItems = cart?.has_physical_items || false;
  const hasDigitalItems = cart?.has_digital_items || false;

  // Fetch cart from server
  const fetchCart = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const cartData = await storeAPI.cart.get(accessToken || undefined);
      setCart(cartData);
    } catch (err) {
      console.error('Failed to fetch cart:', err);
      setError('Failed to load cart');
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  // Load cart on mount and when auth changes
  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  // Merge guest cart when user logs in
  useEffect(() => {
    if (isAuthenticated && accessToken) {
      const guestCart = localStorage.getItem(GUEST_CART_KEY);
      if (guestCart) {
        try {
          const guestItems: GuestCartItem[] = JSON.parse(guestCart);
          // Add guest items to user's cart
          Promise.all(
            guestItems.map(item =>
              storeAPI.cart.add(accessToken, {
                product_id: item.productId,
                variant_id: item.variantId,
                quantity: item.quantity,
              })
            )
          ).then(() => {
            localStorage.removeItem(GUEST_CART_KEY);
            fetchCart();
          }).catch(console.error);
        } catch {
          localStorage.removeItem(GUEST_CART_KEY);
        }
      }
    }
  }, [isAuthenticated, accessToken, fetchCart]);

  // Add item to cart
  const addItem = async (productId: number, variantId?: number, quantity: number = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      const updatedCart = await storeAPI.cart.add(accessToken || undefined, {
        product_id: productId,
        variant_id: variantId,
        quantity,
      });

      setCart(updatedCart);
      setIsOpen(true); // Open cart sidebar when item is added
    } catch (err) {
      console.error('Failed to add item to cart:', err);
      setError('Failed to add item to cart');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Update item quantity
  const updateQuantity = async (itemId: number, quantity: number) => {
    if (quantity < 1) {
      return removeItem(itemId);
    }

    try {
      setIsLoading(true);
      setError(null);

      const updatedCart = await storeAPI.cart.updateItem(accessToken || undefined, itemId, {
        quantity,
      });

      setCart(updatedCart);
    } catch (err) {
      console.error('Failed to update cart item:', err);
      setError('Failed to update cart');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Remove item from cart
  const removeItem = async (itemId: number) => {
    try {
      setIsLoading(true);
      setError(null);

      const updatedCart = await storeAPI.cart.removeItem(accessToken || undefined, itemId);
      setCart(updatedCart);
    } catch (err) {
      console.error('Failed to remove cart item:', err);
      setError('Failed to remove item');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Clear entire cart
  const clearCart = async () => {
    try {
      setIsLoading(true);
      setError(null);

      await storeAPI.cart.clear(accessToken || undefined);
      setCart(null);
    } catch (err) {
      console.error('Failed to clear cart:', err);
      setError('Failed to clear cart');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Cart sidebar controls
  const openCart = () => setIsOpen(true);
  const closeCart = () => setIsOpen(false);
  const toggleCart = () => setIsOpen(prev => !prev);

  // Refresh cart from server
  const refreshCart = async () => {
    await fetchCart();
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        items,
        itemCount,
        subtotal,
        subtotalDollars,
        hasPhysicalItems,
        hasDigitalItems,
        isLoading,
        isOpen,
        error,
        addItem,
        updateQuantity,
        removeItem,
        clearCart,
        openCart,
        closeCart,
        toggleCart,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
