// Property Exchange Types

export interface ProspectorProfile {
  id: number;
  user: number;
  username: string;
  display_name: string;
  company_name: string;
  bio: string;
  years_experience: number;
  specializations: string[];
  regions_active: string[];
  certifications: string[];
  website_url: string;
  contact_email: string;
  phone: string;
  profile_photo_url: string | null;
  is_verified: boolean;
  total_listings: number;
  active_listings: number;
  total_views: number;
  avg_response_time: number;
  created_at: string;
  updated_at: string;
  listings_count: number;
}

export interface PropertyMedia {
  id: number;
  listing: number;
  media_type: 'image' | 'document' | 'video' | 'map';
  category: 'hero' | 'gallery' | 'geological_map' | 'claim_map' | 'location_map' | 'assay' | 'report' | 'permit' | 'other';
  file_url: string;
  thumbnail_url: string | null;
  title: string;
  description: string;
  is_primary: boolean;
  display_order: number;
  file_size_mb?: number;
  file_format?: string;
  sort_order?: number;
  uploaded_at?: string;
  created_at: string;
}

export interface PropertyListing {
  id: number;
  prospector: ProspectorProfile;
  slug: string;
  title: string;
  status: 'draft' | 'pending' | 'active' | 'under_contract' | 'sold' | 'withdrawn';
  listing_type: 'sale' | 'joint_venture' | 'option' | 'lease';
  property_type: 'claim' | 'lease' | 'fee_simple' | 'royalty';

  // Location
  country: string;
  country_display: string;
  province_state: string;
  province_state_display: string;
  nearest_town: string;
  coordinates_lat: number | null;
  coordinates_lng: number | null;
  location_description: string;

  // Claim details
  claim_numbers: string[];
  total_claims: number;
  total_hectares: number;
  total_acres: number;
  mineral_rights_type: 'placer' | 'lode' | 'both';
  mineral_rights_type_display: string;
  surface_rights_included: boolean;
  expiry_date: string | null;
  annual_fees: number | null;

  // Minerals & geology
  primary_mineral: string;
  primary_mineral_display: string;
  secondary_minerals: string[];
  deposit_type: string;
  deposit_type_display: string;
  geological_setting: string;
  mineralization_style: string;
  exploration_stage: string;
  exploration_stage_display: string;

  // Technical data
  assay_highlights: Array<{
    sample_id: string;
    mineral: string;
    grade: string;
    unit: string;
  }>;
  has_43_101_report: boolean;
  has_drilling: boolean;
  drill_hole_count: number | null;
  total_meters_drilled: number | null;
  resource_estimate_oz: number | null;
  resource_category: string;
  historical_production: string;

  // Work completed
  work_completed: Array<{
    year: string;
    type: string;
    description: string;
  }>;

  // Infrastructure
  road_access: string;
  road_access_display: string;
  power_available: boolean;
  water_available: boolean;
  camp_infrastructure: boolean;
  permits_in_place: string[];
  environmental_status: string;

  // Transaction terms
  asking_price: number | null;
  price_currency: string;
  open_to_offers: boolean;
  nsr_royalty: number | null;
  buyback_terms: string;
  work_commitments: string;

  // Content
  summary: string;
  description: string;
  investment_highlights: string[];

  // Stats
  views_count: number;
  inquiries_count: number;
  watchlist_count: number;
  is_featured: boolean;
  featured_until: string | null;

  // Media
  media: PropertyMedia[];
  hero_image: string | null;

  // User-specific
  is_owner?: boolean;
  is_watchlisted?: boolean;

  // Timestamps
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface PropertyListingListItem {
  id: number;
  slug: string;
  title: string;
  status: string;
  listing_type: string;
  listing_type_display: string;
  property_type: string;
  property_type_display: string;
  country: string;
  country_display: string;
  province_state: string;
  total_hectares: number;
  total_acres: number;
  primary_mineral: string;
  primary_mineral_display: string;
  exploration_stage: string;
  exploration_stage_display: string;
  asking_price: number | null;
  price_currency: string;
  open_to_offers: boolean;
  hero_image: string | null;
  prospector_name: string;
  prospector_id: number;
  views_count: number;
  is_featured: boolean;
  is_watchlisted: boolean;
  created_at: string;
}

export interface PropertyInquiry {
  id: number;
  listing: PropertyListingListItem;
  inquirer: {
    id: number;
    username: string;
    full_name: string;
    email: string;
    user_type: string;
  };
  inquiry_type: 'general' | 'site_visit' | 'offer' | 'technical' | 'documents';
  inquiry_type_display: string;
  status: 'new' | 'read' | 'responded' | 'closed';
  status_display: string;
  subject: string;
  message: string;
  response: string | null;
  created_at: string;
  updated_at: string;
}

export interface PropertyWatchlistItem {
  id: number;
  listing: PropertyListingListItem;
  notes: string;
  alert_on_price_change: boolean;
  alert_on_status_change: boolean;
  created_at: string;
}

export interface SavedPropertySearch {
  id: number;
  name: string;
  search_criteria: {
    mineral?: string;
    country?: string;
    province?: string;
    min_price?: number;
    max_price?: number;
    min_size?: number;
    max_size?: number;
    property_type?: string;
    listing_type?: string;
    exploration_stage?: string;
    search?: string;
  };
  alert_frequency: 'none' | 'daily' | 'weekly' | 'instant';
  is_active: boolean;
  last_notified_at: string | null;
  created_at: string;
}

export interface PropertyChoices {
  property_types: Array<{ value: string; label: string }>;
  listing_types: Array<{ value: string; label: string }>;
  mineral_types: Array<{ value: string; label: string }>;
  mineral_rights_types: Array<{ value: string; label: string }>;
  deposit_types: Array<{ value: string; label: string }>;
  exploration_stages: Array<{ value: string; label: string }>;
  access_types: Array<{ value: string; label: string }>;
  countries: Array<{ value: string; label: string }>;
  canadian_provinces: Array<{ value: string; label: string }>;
  us_states?: Array<{ value: string; label: string }>;
  australian_states?: Array<{ value: string; label: string }>;
}

export interface PropertySearchFilters {
  mineral?: string;
  country?: string;
  province?: string;
  property_type?: string;
  listing_type?: string;
  stage?: string;
  min_price?: number;
  max_price?: number;
  min_size?: number;
  max_size?: number;
  has_43_101?: boolean;
  open_to_offers?: boolean;
  search?: string;
  sort?: string;
}
