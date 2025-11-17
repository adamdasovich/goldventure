// Company Types
export interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
  exchange: string;
  description: string;
  website: string;
  headquarters_country: string;
  ceo: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  project_count?: number;
}

// Project Types
export interface Project {
  id: number;
  company: number;
  company_name?: string;
  company_ticker?: string;
  name: string;
  location: string;
  country: string;
  stage: 'exploration' | 'development' | 'production';
  primary_commodity: 'gold' | 'silver' | 'copper' | 'other';
  ownership_percent: number;
  is_flagship: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  resource_count?: number;
}

// Resource Estimate Types
export interface ResourceEstimate {
  id: number;
  project: number;
  project_name?: string;
  category: 'measured' | 'indicated' | 'inferred';
  commodity: string;
  tonnage: number;
  grade: number;
  grade_unit: string;
  contained_metal: number;
  metal_unit: string;
  report_date: string;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

// Economic Study Types
export interface EconomicStudy {
  id: number;
  project: number;
  project_name?: string;
  study_type: 'scoping' | 'pea' | 'prefeasibility' | 'feasibility';
  date_published: string;
  npv_5: number;
  npv_8: number;
  irr: number;
  payback_period: number;
  capex_initial: number;
  capex_sustaining: number;
  opex_per_tonne: number;
  mine_life_years: number;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

// Financing Types
export interface Financing {
  id: number;
  company: number;
  company_name?: string;
  financing_type: 'private_placement' | 'public_offering' | 'debt' | 'royalty' | 'other';
  amount_raised: number;
  currency: string;
  price_per_share: number;
  date_closed: string;
  created_at: string;
  updated_at: string;
}

// Market Data Types
export interface MarketData {
  id: number;
  company: number;
  company_name?: string;
  ticker?: string;
  date: string;
  close_price: number;
  volume: number;
  market_cap: number;
  shares_outstanding: number;
  created_at: string;
}

// Claude Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ToolCall {
  tool: string;
  input: Record<string, any>;
  result: any;
}

export interface ChatResponse {
  message: string;
  tool_calls: ToolCall[];
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
  conversation_history: ChatMessage[];
}

export interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
  system_prompt?: string;
}
