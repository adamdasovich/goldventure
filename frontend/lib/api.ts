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
    headers: {
      'Content-Type': 'application/json',
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

  getTools: () =>
    apiFetch<{ tools: any[]; count: number }>('/claude/tools/'),
};
