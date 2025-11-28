import type {
  Company,
  Project,
  ResourceEstimate,
  Financing,
  ChatRequest,
  ChatResponse
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

// Claude Chat API
export const claudeAPI = {
  chat: (request: ChatRequest) =>
    apiFetch<ChatResponse>('/claude/chat/', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

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
