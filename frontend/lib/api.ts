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
  BillingPortalResponse
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
    apiFetch<void>(`/company-portal/resources/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${accessToken}` }
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
  BillingPortalResponse
} from '@/types/api';
