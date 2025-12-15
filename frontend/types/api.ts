// Company Types
export interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
  exchange: string;
  description: string;
  website: string;
  headquarters: string;
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
  project_stage: string;
  primary_commodity: string;
  country: string;
  province_state: string;
  latitude: number | null;
  longitude: number | null;
  description: string;
  ownership_percentage: number;
  acquisition_date: string | null;
  last_drill_program: string | null;
  is_flagship: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  resource_count?: number;
  total_resources_oz?: number;
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

// Company Portal Types
export interface CompanyResource {
  id: number;
  company: number;
  company_name?: string;
  project?: number;
  project_name?: string;
  resource_type: 'image' | 'video' | 'document' | 'presentation' | 'spreadsheet' | 'other';
  category: 'hero' | 'gallery' | 'investor_presentation' | 'technical_report' | 'map' | 'logo' | 'news_image' | 'other';
  title: string;
  description?: string;
  file?: string;
  file_url?: string;
  external_url?: string;
  thumbnail_url?: string;
  file_size?: number;
  mime_type?: string;
  is_public: boolean;
  is_featured: boolean;
  display_order: number;
  uploaded_by?: number;
  uploaded_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface SpeakingEvent {
  id: number;
  company: number;
  company_name?: string;
  event_type: 'conference' | 'webinar' | 'investor_day' | 'site_visit' | 'earnings_call' | 'presentation' | 'interview' | 'other';
  title: string;
  description?: string;
  event_date: string;
  event_end_date?: string;
  timezone: string;
  location?: string;
  venue_name?: string;
  is_virtual: boolean;
  virtual_link?: string;
  registration_url?: string;
  presentation_url?: string;
  speakers?: string;
  is_published: boolean;
  is_featured: boolean;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled' | 'unpaid' | 'incomplete' | 'incomplete_expired' | 'paused';

export interface CompanySubscription {
  id: number;
  company: number;
  company_name?: string;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  status: SubscriptionStatus;
  current_period_start?: string;
  current_period_end?: string;
  trial_start?: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
  canceled_at?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  days_until_trial_end?: number;
}

export interface SubscriptionInvoice {
  id: number;
  subscription: number;
  stripe_invoice_id?: string;
  amount_due: number;
  amount_paid: number;
  currency: string;
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void';
  invoice_date: string;
  due_date?: string;
  paid_at?: string;
  invoice_pdf?: string;
  hosted_invoice_url?: string;
  created_at: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export interface BillingPortalResponse {
  portal_url: string;
}

// Company Access Request Types
export type AccessRequestStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';
export type AccessRequestRole = 'ir_manager' | 'ceo' | 'cfo' | 'marketing' | 'communications' | 'other';

export interface CompanyAccessRequest {
  id: number;
  user: number;
  user_name?: string;
  user_email?: string;
  company: number;
  company_name?: string;
  company_ticker?: string;
  status: AccessRequestStatus;
  status_display?: string;
  role: AccessRequestRole;
  role_display?: string;
  job_title: string;
  justification: string;
  work_email: string;
  reviewer?: number;
  reviewer_name?: string;
  review_notes?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyAccessRequestCreate {
  company: number;
  role: AccessRequestRole;
  job_title: string;
  justification: string;
  work_email: string;
}

export interface MyRequestResponse {
  has_pending_request: boolean;
  has_company: boolean;
  company_name?: string;
}

export interface AccessRequestChoices {
  roles: { value: string; label: string }[];
  statuses: { value: string; label: string }[];
}
