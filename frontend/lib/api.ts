import type {
  Company,
  Project,
  ResourceEstimate,
  Financing,
  ChatRequest,
  ChatResponse,
  CompanyResource,
  SpeakingEvent,
  CompanySubscription,
  SubscriptionInvoice,
  CheckoutSessionResponse,
  BillingPortalResponse,
  // Store types
  StoreCategory,
  StoreProductList,
  StoreProductDetail,
  StoreProductImage,
  StoreProductVariant,
  StoreCart,
  StoreCartItem,
  StoreOrder,
  StoreOrderItem,
  StoreShippingRate,
  StoreRecentPurchase,
  StoreProductShare,
  StoreProductInquiry,
  UserStoreBadge,
  ProductBadge,
  OrderStatus,
  InquiryStatus,
  StoreBadgeType,
  ShippingAddress,
  AddToCartRequest,
  UpdateCartItemRequest,
  StoreCheckoutRequest,
  StoreCheckoutResponse,
  CalculateShippingResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Generic fetch wrapper with error handling
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    cache: 'no-store', // Disable Next.js cache
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `API Error: ${response.status}`);
  }

  return response.json();
}

// Company API
export const companyAPI = {
  getAll: (params?: { search?: string; ticker?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return apiFetch<{ results: Company[] }>(`/companies/${query ? `?${query}` : ''}`);
  },

  getById: (id: number) =>
    apiFetch<Company>(`/companies/${id}/`),

  getProjects: (companyId: number) =>
    apiFetch<Project[]>(`/companies/${companyId}/projects/`),
};

// Project API
export const projectAPI = {
  getAll: (params?: { company?: number; commodity?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return apiFetch<{ results: Project[] }>(`/projects/${query ? `?${query}` : ''}`);
  },

  getById: (id: number) =>
    apiFetch<Project>(`/projects/${id}/`),
};

// Resource API
export const resourceAPI = {
  getAll: () =>
    apiFetch<{ results: ResourceEstimate[] }>('/resources/'),

  getById: (id: number) =>
    apiFetch<ResourceEstimate>(`/resources/${id}/`),
};

// Financing API
export const financingAPI = {
  getAll: () =>
    apiFetch<{ results: Financing[] }>('/financings/'),

  getById: (id: number) =>
    apiFetch<Financing>(`/financings/${id}/`),

  delete: (accessToken: string, id: number) =>
    fetch(`${API_BASE_URL}/financings/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }).then(res => {
      if (!res.ok) throw new Error('Failed to delete financing');
      // DELETE returns 204 No Content - don't try to parse JSON
      return;
    }),
};

// Claude Chat API - Uses local Next.js API route to avoid CORS issues
export const claudeAPI = {
  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    // Use local API route to proxy to backend (avoids CORS issues)
    const response = await fetch('/api/claude/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Network error' }));
      throw new Error(error.error || `API Error: ${response.status}`);
    }

    return response.json();
  },

  companyChat: (companyId: number, request: ChatRequest) =>
    apiFetch<ChatResponse>(`/companies/${companyId}/chat/`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  getTools: () =>
    apiFetch<{ tools: any[]; count: number }>('/claude/tools/'),
};

// Metals Pricing API
export interface MetalPrice {
  metal: string;
  symbol: string;
  price: number | null;
  change_percent: number;
  unit: string;
  currency: string;
  last_updated: string;
  error?: string;
}

export interface MetalPricesResponse {
  metals: MetalPrice[];
  timestamp: string;
  cached: boolean;
}

export interface HistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MetalHistoricalResponse {
  symbol: string;
  data: HistoricalDataPoint[];
  days: number;
  timestamp: string;
}

export const metalsAPI = {
  getPrices: () =>
    apiFetch<MetalPricesResponse>('/metals/prices/'),

  getHistorical: (symbol: string, days?: number) => {
    const query = days ? `?days=${days}` : '';
    return apiFetch<MetalHistoricalResponse>(`/metals/historical/${symbol}/${query}`);
  },
};

// News Releases API
export interface NewsRelease {
  id: number;
  company: number;
  company_name?: string;
  project?: number | null;
  title: string;
  release_type: string;
  release_date: string;
  summary: string;
  full_text: string;
  url: string;
  is_material: boolean;
  created_at: string;
  updated_at: string;
}

export interface NewsReleasesResponse {
  financial: NewsRelease[];
  non_financial: NewsRelease[];
  last_updated: string | null;
  financial_count: number;
  non_financial_count: number;
}

export interface ScrapeNewsResponse {
  status: string;
  message: string;
  financial_count: number;
  non_financial_count: number;
  last_scraped: string;
  error?: string;
}

export const newsAPI = {
  getNewsReleases: (companyId: number) =>
    apiFetch<NewsReleasesResponse>(`/companies/${companyId}/news-releases/`),

  scrapeNews: (companyId: number) =>
    apiFetch<ScrapeNewsResponse>(`/companies/${companyId}/scrape-news/`, {
      method: 'POST',
    }),
};

// Company Portal - Resources API
export const companyResourceAPI = {
  getAll: (accessToken: string, params?: { company?: number; category?: string; is_public?: boolean }) => {
    const query = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
    return apiFetch<{ results: CompanyResource[] }>(`/company-portal/resources/${query ? `?${query}` : ''}`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
  },

  getById: (accessToken: string, id: number) =>
    apiFetch<CompanyResource>(`/company-portal/resources/${id}/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  create: (accessToken: string, formData: FormData) =>
    fetch(`${API_BASE_URL}/company-portal/resources/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: formData, // FormData for file uploads - don't set Content-Type
    }).then(res => {
      if (!res.ok) throw new Error('Failed to create resource');
      return res.json() as Promise<CompanyResource>;
    }),

  update: (accessToken: string, id: number, formData: FormData) =>
    fetch(`${API_BASE_URL}/company-portal/resources/${id}/`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: formData,
    }).then(res => {
      if (!res.ok) throw new Error('Failed to update resource');
      return res.json() as Promise<CompanyResource>;
    }),

  delete: (accessToken: string, id: number) =>
    fetch(`${API_BASE_URL}/company-portal/resources/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }).then(res => {
      if (!res.ok) throw new Error('Failed to delete resource');
      // DELETE returns 204 No Content - don't try to parse JSON
      return;
    }),

  getMyResources: (accessToken: string) =>
    apiFetch<{ results: CompanyResource[] }>(`/company-portal/resources/my_resources/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  getByCategory: (accessToken: string, category: string) =>
    apiFetch<{ results: CompanyResource[] }>(`/company-portal/resources/by_category/?category=${category}`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),
};

// Company Portal - Speaking Events API
export const speakingEventAPI = {
  getAll: (params?: { company?: number; event_type?: string; is_published?: boolean }) => {
    const query = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
    return apiFetch<{ results: SpeakingEvent[] }>(`/company-portal/events/${query ? `?${query}` : ''}`);
  },

  getById: (id: number) =>
    apiFetch<SpeakingEvent>(`/company-portal/events/${id}/`),

  create: (accessToken: string, data: Partial<SpeakingEvent>) =>
    apiFetch<SpeakingEvent>(`/company-portal/events/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify(data),
    }),

  update: (accessToken: string, id: number, data: Partial<SpeakingEvent>) =>
    apiFetch<SpeakingEvent>(`/company-portal/events/${id}/`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify(data),
    }),

  delete: (accessToken: string, id: number) =>
    apiFetch<void>(`/company-portal/events/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  getMyEvents: (accessToken: string) =>
    apiFetch<{ results: SpeakingEvent[] }>(`/company-portal/events/my_events/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  getUpcoming: () =>
    apiFetch<{ results: SpeakingEvent[] }>(`/company-portal/events/upcoming/`),

  publish: (accessToken: string, id: number) =>
    apiFetch<SpeakingEvent>(`/company-portal/events/${id}/publish/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  unpublish: (accessToken: string, id: number) =>
    apiFetch<SpeakingEvent>(`/company-portal/events/${id}/unpublish/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),
};

// Company Portal - Subscription API
export const subscriptionAPI = {
  getMySubscription: (accessToken: string) =>
    apiFetch<CompanySubscription>(`/company-portal/subscriptions/my_subscription/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  getInvoices: (accessToken: string) =>
    apiFetch<{ results: SubscriptionInvoice[] }>(`/company-portal/subscriptions/invoices/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  createCheckout: (accessToken: string, successUrl: string, cancelUrl: string) =>
    apiFetch<CheckoutSessionResponse>(`/company-portal/subscriptions/create-checkout/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify({ success_url: successUrl, cancel_url: cancelUrl }),
    }),

  openBillingPortal: (accessToken: string, returnUrl: string) =>
    apiFetch<BillingPortalResponse>(`/company-portal/subscriptions/billing-portal/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify({ return_url: returnUrl }),
    }),

  cancel: (accessToken: string) =>
    apiFetch<CompanySubscription>(`/company-portal/subscriptions/cancel/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  reactivate: (accessToken: string) =>
    apiFetch<CompanySubscription>(`/company-portal/subscriptions/reactivate/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),
};

// Company Portal - Access Request API
import type {
  CompanyAccessRequest,
  CompanyAccessRequestCreate,
  MyRequestResponse,
  AccessRequestChoices
} from '@/types/api';

export const accessRequestAPI = {
  // Get current user's pending request or status
  getMyRequest: (accessToken: string) =>
    apiFetch<CompanyAccessRequest | MyRequestResponse>(`/company-portal/access-requests/my_request/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  // Get all user's requests
  getAll: (accessToken: string) =>
    apiFetch<{ results: CompanyAccessRequest[] }>(`/company-portal/access-requests/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  // Create a new access request
  create: (accessToken: string, data: CompanyAccessRequestCreate) =>
    apiFetch<CompanyAccessRequest>(`/company-portal/access-requests/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify(data),
    }),

  // Cancel a pending request
  cancel: (accessToken: string, requestId: number) =>
    apiFetch<void>(`/company-portal/access-requests/${requestId}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  // Get dropdown choices
  getChoices: (accessToken: string) =>
    apiFetch<AccessRequestChoices>(`/company-portal/access-requests/choices/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  // Admin: Get all pending requests
  getPending: (accessToken: string) =>
    apiFetch<{ results: CompanyAccessRequest[]; count: number }>(`/company-portal/access-requests/pending/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }),

  // Admin: Review (approve/reject) a request
  review: (accessToken: string, requestId: number, action: 'approve' | 'reject', notes?: string) =>
    apiFetch<{ message: string; request: CompanyAccessRequest }>(`/company-portal/access-requests/${requestId}/review/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify({ action, notes: notes || '' }),
    }),
};

// ============================================================================
// STORE API
// ============================================================================

export interface StoreProductFilters {
  category?: string;
  product_type?: 'physical' | 'digital';
  badge?: string;
  min_price?: number;
  max_price?: number;
  ordering?: 'price_cents' | '-price_cents' | '-created_at' | '-total_sold';
  search?: string;
}

export const storeAPI = {
  // Categories
  categories: {
    getAll: () =>
      apiFetch<{ results: StoreCategory[] }>('/store/categories/'),

    getBySlug: (slug: string) =>
      apiFetch<StoreCategory>(`/store/categories/${slug}/`),
  },

  // Products
  products: {
    getAll: (filters?: StoreProductFilters) => {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) params.append(key, String(value));
        });
      }
      const query = params.toString();
      return apiFetch<{ results: StoreProductList[]; count: number }>(`/store/products/${query ? `?${query}` : ''}`);
    },

    getBySlug: (slug: string) =>
      apiFetch<StoreProductDetail>(`/store/products/${slug}/`),

    getFeatured: () =>
      apiFetch<{ results: StoreProductList[] }>('/store/products/featured/'),

    getByCategory: (categorySlug: string) =>
      apiFetch<{ results: StoreProductList[] }>(`/store/products/?category=${categorySlug}`),

    share: (accessToken: string, productId: number, sharedTo: 'forum' | 'inquiry' | 'direct_message', destinationId: string) =>
      apiFetch<{ id: number; message: string }>(`/store/products/${productId}/share/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: JSON.stringify({ shared_to: sharedTo, destination_id: destinationId }),
      }),

    inquire: (accessToken: string, productId: number, message: string, phone?: string, preferredContact?: 'email' | 'phone') =>
      apiFetch<StoreProductInquiry>(`/store/products/${productId}/inquire/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: JSON.stringify({ message, phone, preferred_contact: preferredContact || 'email' }),
      }),
  },

  // Cart
  cart: {
    get: (accessToken?: string) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<StoreCart>('/store/cart/', { headers });
    },

    add: (accessToken: string | undefined, item: AddToCartRequest) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<StoreCart>('/store/cart/add/', {
        method: 'POST',
        headers,
        body: JSON.stringify(item),
      });
    },

    updateItem: (accessToken: string | undefined, itemId: number, data: UpdateCartItemRequest) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<StoreCart>(`/store/cart/${itemId}/update_item/`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data),
      });
    },

    removeItem: (accessToken: string | undefined, itemId: number) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<StoreCart>(`/store/cart/${itemId}/remove_item/`, {
        method: 'DELETE',
        headers,
      });
    },

    clear: (accessToken: string | undefined) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<{ message: string }>('/store/cart/clear/', {
        method: 'POST',
        headers,
      });
    },
  },

  // Orders
  orders: {
    getAll: (accessToken: string) =>
      apiFetch<{ results: StoreOrder[] }>('/store/orders/', {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      }),

    getById: (accessToken: string, orderId: number) =>
      apiFetch<StoreOrder>(`/store/orders/${orderId}/`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      }),
  },

  // Shipping
  shipping: {
    getRates: () =>
      apiFetch<{ results: StoreShippingRate[] }>('/store/shipping-rates/'),

    calculate: (accessToken: string | undefined, country: string) => {
      const headers: Record<string, string> = {};
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      return apiFetch<CalculateShippingResponse>(`/store/shipping-rates/calculate/?country=${country}`, {
        headers,
      });
    },
  },

  // Checkout
  checkout: (accessToken: string, data: StoreCheckoutRequest) =>
    apiFetch<StoreCheckoutResponse>('/store/checkout/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify(data),
    }),

  // Ticker (recent purchases)
  ticker: {
    getRecent: (limit?: number) => {
      const query = limit ? `?limit=${limit}` : '';
      return apiFetch<{ results: StoreRecentPurchase[] }>(`/store/ticker/${query}`);
    },
  },

  // User badges
  badges: {
    getMy: (accessToken: string) =>
      apiFetch<{ results: UserStoreBadge[] }>('/store/badges/', {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      }),
  },
};

// Re-export types for convenience
export type {
  Company,
  Project,
  ResourceEstimate,
  Financing,
  ChatRequest,
  ChatResponse,
  ChatMessage,
  CompanyResource,
  SpeakingEvent,
  CompanySubscription,
  SubscriptionInvoice,
  CheckoutSessionResponse,
  BillingPortalResponse,
  CompanyAccessRequest,
  CompanyAccessRequestCreate,
  MyRequestResponse,
  AccessRequestChoices,
  // Store types
  StoreCategory,
  StoreProductList,
  StoreProductDetail,
  StoreProductImage,
  StoreProductVariant,
  StoreCart,
  StoreCartItem,
  StoreOrder,
  StoreOrderItem,
  StoreShippingRate,
  StoreRecentPurchase,
  StoreProductShare,
  StoreProductInquiry,
  UserStoreBadge,
  ProductBadge,
  OrderStatus,
  InquiryStatus,
  StoreBadgeType,
  ShippingAddress,
  AddToCartRequest,
  UpdateCartItemRequest,
  StoreCheckoutRequest,
  StoreCheckoutResponse,
  CalculateShippingResponse,
} from '@/types/api';
