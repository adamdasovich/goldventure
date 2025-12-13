'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyChoices } from '@/types/property';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

interface FormData {
  // Basic Info
  title: string;
  listing_type: string;
  property_type: string;
  summary: string;
  description: string;

  // Location
  country: string;
  province_state: string;
  nearest_town: string;
  coordinates_lat: string;
  coordinates_lng: string;
  location_description: string;

  // Claim Details
  claim_numbers: string;
  total_claims: string;
  total_hectares: string;
  mineral_rights_type: string;
  surface_rights_included: boolean;
  expiry_date: string;
  annual_fees: string;

  // Minerals & Geology
  primary_mineral: string;
  secondary_minerals: string;
  deposit_type: string;
  geological_setting: string;
  mineralization_style: string;
  exploration_stage: string;

  // Technical Data
  has_43_101_report: boolean;
  has_drilling: boolean;
  drill_hole_count: string;
  total_meters_drilled: string;
  resource_estimate_oz: string;
  resource_category: string;
  historical_production: string;

  // Infrastructure
  road_access: string;
  power_available: boolean;
  water_available: boolean;
  camp_infrastructure: boolean;
  environmental_status: string;

  // Transaction Terms
  asking_price: string;
  price_currency: string;
  open_to_offers: boolean;
  nsr_royalty: string;
  buyback_terms: string;
  work_commitments: string;

  // Investment Highlights
  investment_highlights: string;
}

const initialFormData: FormData = {
  title: '',
  listing_type: 'sale',
  property_type: 'claim',
  summary: '',
  description: '',
  country: 'CA',
  province_state: '',
  nearest_town: '',
  coordinates_lat: '',
  coordinates_lng: '',
  location_description: '',
  claim_numbers: '',
  total_claims: '',
  total_hectares: '',
  mineral_rights_type: 'lode',
  surface_rights_included: false,
  expiry_date: '',
  annual_fees: '',
  primary_mineral: 'gold',
  secondary_minerals: '',
  deposit_type: '',
  geological_setting: '',
  mineralization_style: '',
  exploration_stage: 'grassroots',
  has_43_101_report: false,
  has_drilling: false,
  drill_hole_count: '',
  total_meters_drilled: '',
  resource_estimate_oz: '',
  resource_category: '',
  historical_production: '',
  road_access: 'all_season',
  power_available: false,
  water_available: false,
  camp_infrastructure: false,
  environmental_status: '',
  asking_price: '',
  price_currency: 'CAD',
  open_to_offers: true,
  nsr_royalty: '',
  buyback_terms: '',
  work_commitments: '',
  investment_highlights: '',
};

const STEPS = [
  { id: 1, name: 'Basic Info', description: 'Property title and description' },
  { id: 2, name: 'Location', description: 'Where is the property?' },
  { id: 3, name: 'Claims', description: 'Claim details and size' },
  { id: 4, name: 'Geology', description: 'Minerals and exploration data' },
  { id: 5, name: 'Technical', description: 'Drilling and reports' },
  { id: 6, name: 'Infrastructure', description: 'Access and facilities' },
  { id: 7, name: 'Terms', description: 'Price and transaction details' },
  { id: 8, name: 'Review', description: 'Review and submit' },
];

export default function NewPropertyPage() {
  const router = useRouter();
  const { user, accessToken, isLoading: authLoading } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [choices, setChoices] = useState<PropertyChoices | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agreementAccepted, setAgreementAccepted] = useState<boolean | null>(null);
  const [checkingAgreement, setCheckingAgreement] = useState(true);

  // Check if user has accepted commission agreement
  useEffect(() => {
    const checkAgreement = async () => {
      if (!accessToken) {
        setCheckingAgreement(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/properties/prospectors/my_agreements/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const agreements = await response.json();
          setAgreementAccepted(agreements.length > 0);
        } else {
          setAgreementAccepted(false);
        }
      } catch {
        setAgreementAccepted(false);
      } finally {
        setCheckingAgreement(false);
      }
    };

    if (!authLoading) {
      checkAgreement();
    }
  }, [accessToken, authLoading]);

  // Fetch choices
  useEffect(() => {
    const fetchChoices = async () => {
      try {
        const response = await fetch(`${API_URL}/properties/listings/choices/`);
        if (response.ok) {
          const data = await response.json();
          setChoices(data);
        }
      } catch (err) {
        console.error('Failed to fetch choices:', err);
      }
    };
    fetchChoices();
  }, []);

  const updateField = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getProvinceOptions = () => {
    if (!choices) return [];
    switch (formData.country) {
      case 'CA':
        return choices.canadian_provinces || [];
      case 'US':
        return choices.us_states || [];
      case 'AU':
        return choices.australian_states || [];
      default:
        return [];
    }
  };

  const handleSubmit = async (isDraft: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      // Prepare the data
      const submitData = {
        title: formData.title,
        listing_type: formData.listing_type,
        property_type: formData.property_type,
        summary: formData.summary,
        description: formData.description,
        country: formData.country,
        province_state: formData.province_state,
        nearest_town: formData.nearest_town,
        coordinates_lat: formData.coordinates_lat ? parseFloat(formData.coordinates_lat) : null,
        coordinates_lng: formData.coordinates_lng ? parseFloat(formData.coordinates_lng) : null,
        location_description: formData.location_description,
        claim_numbers: formData.claim_numbers.split(',').map(s => s.trim()).filter(Boolean),
        total_claims: formData.total_claims ? parseInt(formData.total_claims) : null,
        total_hectares: formData.total_hectares ? parseFloat(formData.total_hectares) : null,
        mineral_rights_type: formData.mineral_rights_type,
        surface_rights_included: formData.surface_rights_included,
        expiry_date: formData.expiry_date || null,
        annual_fees: formData.annual_fees ? parseFloat(formData.annual_fees) : null,
        primary_mineral: formData.primary_mineral,
        secondary_minerals: formData.secondary_minerals.split(',').map(s => s.trim()).filter(Boolean),
        deposit_type: formData.deposit_type,
        geological_setting: formData.geological_setting,
        mineralization_style: formData.mineralization_style,
        exploration_stage: formData.exploration_stage,
        has_43_101_report: formData.has_43_101_report,
        has_drilling: formData.has_drilling,
        drill_hole_count: formData.drill_hole_count ? parseInt(formData.drill_hole_count) : null,
        total_meters_drilled: formData.total_meters_drilled ? parseFloat(formData.total_meters_drilled) : null,
        resource_estimate_oz: formData.resource_estimate_oz ? parseFloat(formData.resource_estimate_oz) : null,
        resource_category: formData.resource_category,
        historical_production: formData.historical_production,
        road_access: formData.road_access,
        power_available: formData.power_available,
        water_available: formData.water_available,
        camp_infrastructure: formData.camp_infrastructure,
        environmental_status: formData.environmental_status,
        asking_price: formData.asking_price ? parseFloat(formData.asking_price) : null,
        price_currency: formData.price_currency,
        open_to_offers: formData.open_to_offers,
        nsr_royalty: formData.nsr_royalty ? parseFloat(formData.nsr_royalty) : null,
        buyback_terms: formData.buyback_terms,
        work_commitments: formData.work_commitments,
        investment_highlights: formData.investment_highlights.split('\n').filter(Boolean),
        status: isDraft ? 'draft' : 'pending_review',
      };

      const response = await fetch(`${API_URL}/properties/listings/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Handle different error formats from Django REST Framework
        let errorMessage = 'Failed to create listing';
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (typeof errorData === 'object') {
          // Field-level validation errors
          const fieldErrors = Object.entries(errorData)
            .map(([field, errors]) => {
              const errorList = Array.isArray(errors) ? errors.join(', ') : String(errors);
              return `${field}: ${errorList}`;
            })
            .join('; ');
          if (fieldErrors) {
            errorMessage = fieldErrors;
          }
        }
        console.error('API Error Response:', errorData);
        throw new Error(errorMessage);
      }

      const listing = await response.json();
      router.push(`/properties/my-listings?created=${listing.slug}`);
    } catch (err) {
      console.error('Failed to create listing:', err);
      setError(err instanceof Error ? err.message : 'Failed to create listing');
    } finally {
      setLoading(false);
    }
  };

  // Redirect if not logged in
  if (!authLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <h1 className="text-2xl font-bold text-white mb-4">Sign In Required</h1>
          <p className="text-slate-300 mb-6">You need to be logged in to list a property.</p>
          <Button variant="primary" onClick={() => router.push('/properties')}>
            Go to Prospector's Exchange
          </Button>
        </Card>
      </div>
    );
  }

  // Show loading while checking agreement
  if (authLoading || checkingAgreement) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  // Show commission agreement if not accepted
  if (agreementAccepted === false) {
    return <CommissionAgreementFlow onAccepted={() => setAgreementAccepted(true)} accessToken={accessToken!} />;
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Property Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => updateField('title', e.target.value)}
                placeholder="e.g., Golden Eagle Gold Property - 120 Claims"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
              <p className="text-sm text-slate-500 mt-1">A descriptive title that includes key details</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Listing Type *</label>
                <select
                  value={formData.listing_type}
                  onChange={(e) => updateField('listing_type', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.listing_types?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Property Type *</label>
                <select
                  value={formData.property_type}
                  onChange={(e) => updateField('property_type', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.property_types?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Summary *</label>
              <textarea
                value={formData.summary}
                onChange={(e) => updateField('summary', e.target.value)}
                rows={3}
                placeholder="A brief summary that will appear in search results..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
              <p className="text-sm text-slate-500 mt-1">{formData.summary.length}/300 characters</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Full Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => updateField('description', e.target.value)}
                rows={8}
                placeholder="Detailed description of the property, its history, potential, and any other relevant information..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Country *</label>
                <select
                  value={formData.country}
                  onChange={(e) => {
                    updateField('country', e.target.value);
                    updateField('province_state', '');
                  }}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.countries?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {formData.country === 'US' ? 'State' : 'Province'} *
                </label>
                <select
                  value={formData.province_state}
                  onChange={(e) => updateField('province_state', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {getProvinceOptions().map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Nearest Town/City</label>
              <input
                type="text"
                value={formData.nearest_town}
                onChange={(e) => updateField('nearest_town', e.target.value)}
                placeholder="e.g., Red Lake, ON"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Latitude (optional)</label>
                <input
                  type="text"
                  value={formData.coordinates_lat}
                  onChange={(e) => updateField('coordinates_lat', e.target.value)}
                  placeholder="e.g., 51.0789"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Longitude (optional)</label>
                <input
                  type="text"
                  value={formData.coordinates_lng}
                  onChange={(e) => updateField('coordinates_lng', e.target.value)}
                  placeholder="e.g., -93.8312"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Location Description</label>
              <textarea
                value={formData.location_description}
                onChange={(e) => updateField('location_description', e.target.value)}
                rows={4}
                placeholder="Describe how to access the property, nearby landmarks, etc..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Claim Numbers</label>
              <input
                type="text"
                value={formData.claim_numbers}
                onChange={(e) => updateField('claim_numbers', e.target.value)}
                placeholder="Comma-separated list: 1234567, 1234568, 1234569"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Total Number of Claims</label>
                <input
                  type="number"
                  value={formData.total_claims}
                  onChange={(e) => updateField('total_claims', e.target.value)}
                  placeholder="e.g., 120"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Total Hectares</label>
                <input
                  type="number"
                  value={formData.total_hectares}
                  onChange={(e) => updateField('total_hectares', e.target.value)}
                  placeholder="e.g., 2400"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Mineral Rights Type</label>
                <select
                  value={formData.mineral_rights_type}
                  onChange={(e) => updateField('mineral_rights_type', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.mineral_rights_types?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Claim Expiry Date</label>
                <input
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) => updateField('expiry_date', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Annual Fees (CAD)</label>
                <input
                  type="number"
                  value={formData.annual_fees}
                  onChange={(e) => updateField('annual_fees', e.target.value)}
                  placeholder="e.g., 5000"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center pt-8">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.surface_rights_included}
                    onChange={(e) => updateField('surface_rights_included', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                  />
                  <span className="text-slate-300">Surface Rights Included</span>
                </label>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Primary Mineral *</label>
                <select
                  value={formData.primary_mineral}
                  onChange={(e) => updateField('primary_mineral', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.mineral_types?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Secondary Minerals</label>
                <input
                  type="text"
                  value={formData.secondary_minerals}
                  onChange={(e) => updateField('secondary_minerals', e.target.value)}
                  placeholder="e.g., Silver, Copper (comma-separated)"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Deposit Type</label>
                <select
                  value={formData.deposit_type}
                  onChange={(e) => updateField('deposit_type', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {choices?.deposit_types?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Exploration Stage *</label>
                <select
                  value={formData.exploration_stage}
                  onChange={(e) => updateField('exploration_stage', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  {choices?.exploration_stages?.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Geological Setting</label>
              <textarea
                value={formData.geological_setting}
                onChange={(e) => updateField('geological_setting', e.target.value)}
                rows={3}
                placeholder="Describe the regional and local geology..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Mineralization Style</label>
              <textarea
                value={formData.mineralization_style}
                onChange={(e) => updateField('mineralization_style', e.target.value)}
                rows={3}
                placeholder="Describe the type and style of mineralization..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <input
                  type="checkbox"
                  checked={formData.has_43_101_report}
                  onChange={(e) => updateField('has_43_101_report', e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <div>
                  <span className="text-white font-medium">Has NI 43-101 Report</span>
                  <p className="text-sm text-slate-400">Technical report compliant with Canadian standards</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <input
                  type="checkbox"
                  checked={formData.has_drilling}
                  onChange={(e) => updateField('has_drilling', e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <div>
                  <span className="text-white font-medium">Has Drilling Data</span>
                  <p className="text-sm text-slate-400">Property has been drilled</p>
                </div>
              </label>
            </div>

            {formData.has_drilling && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Number of Drill Holes</label>
                  <input
                    type="number"
                    value={formData.drill_hole_count}
                    onChange={(e) => updateField('drill_hole_count', e.target.value)}
                    placeholder="e.g., 25"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Total Meters Drilled</label>
                  <input
                    type="number"
                    value={formData.total_meters_drilled}
                    onChange={(e) => updateField('total_meters_drilled', e.target.value)}
                    placeholder="e.g., 5000"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Resource Estimate (oz)</label>
                <input
                  type="number"
                  value={formData.resource_estimate_oz}
                  onChange={(e) => updateField('resource_estimate_oz', e.target.value)}
                  placeholder="Gold equivalent ounces"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Resource Category</label>
                <select
                  value={formData.resource_category}
                  onChange={(e) => updateField('resource_category', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  <option value="inferred">Inferred</option>
                  <option value="indicated">Indicated</option>
                  <option value="measured">Measured</option>
                  <option value="probable">Probable Reserve</option>
                  <option value="proven">Proven Reserve</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Historical Production</label>
              <textarea
                value={formData.historical_production}
                onChange={(e) => updateField('historical_production', e.target.value)}
                rows={3}
                placeholder="Describe any historical production or past mining activity..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Road Access</label>
              <select
                value={formData.road_access}
                onChange={(e) => updateField('road_access', e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              >
                {choices?.access_types?.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <input
                  type="checkbox"
                  checked={formData.power_available}
                  onChange={(e) => updateField('power_available', e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <span className="text-slate-300">Power Available</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <input
                  type="checkbox"
                  checked={formData.water_available}
                  onChange={(e) => updateField('water_available', e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <span className="text-slate-300">Water Available</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                <input
                  type="checkbox"
                  checked={formData.camp_infrastructure}
                  onChange={(e) => updateField('camp_infrastructure', e.target.checked)}
                  className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <span className="text-slate-300">Camp Infrastructure</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Environmental Status</label>
              <textarea
                value={formData.environmental_status}
                onChange={(e) => updateField('environmental_status', e.target.value)}
                rows={3}
                placeholder="Describe environmental considerations, permits, or assessments..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 7:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Asking Price</label>
                <input
                  type="number"
                  value={formData.asking_price}
                  onChange={(e) => updateField('asking_price', e.target.value)}
                  placeholder="Leave blank for 'Contact for Price'"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Currency</label>
                <select
                  value={formData.price_currency}
                  onChange={(e) => updateField('price_currency', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                >
                  <option value="CAD">CAD - Canadian Dollar</option>
                  <option value="USD">USD - US Dollar</option>
                  <option value="AUD">AUD - Australian Dollar</option>
                </select>
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <input
                type="checkbox"
                checked={formData.open_to_offers}
                onChange={(e) => updateField('open_to_offers', e.target.checked)}
                className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
              />
              <div>
                <span className="text-white font-medium">Open to Offers</span>
                <p className="text-sm text-slate-400">Indicate that you're willing to negotiate</p>
              </div>
            </label>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">NSR Royalty (%)</label>
              <input
                type="number"
                step="0.5"
                value={formData.nsr_royalty}
                onChange={(e) => updateField('nsr_royalty', e.target.value)}
                placeholder="e.g., 2.0"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
              <p className="text-sm text-slate-500 mt-1">Net Smelter Return royalty retained, if any</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Buyback Terms</label>
              <textarea
                value={formData.buyback_terms}
                onChange={(e) => updateField('buyback_terms', e.target.value)}
                rows={2}
                placeholder="e.g., 1% NSR buyback for $1,000,000"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Work Commitments</label>
              <textarea
                value={formData.work_commitments}
                onChange={(e) => updateField('work_commitments', e.target.value)}
                rows={2}
                placeholder="Any required work commitments or expenditures..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Investment Highlights</label>
              <textarea
                value={formData.investment_highlights}
                onChange={(e) => updateField('investment_highlights', e.target.value)}
                rows={4}
                placeholder="Enter each highlight on a new line:&#10;- Near-surface gold mineralization&#10;- Road accessible year-round&#10;- Past producer with historical grades"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>
          </div>
        );

      case 8:
        return (
          <div className="space-y-6">
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-semibold text-white mb-4">Review Your Listing</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Basic Info</h4>
                  <p className="text-white font-medium">{formData.title || 'Untitled'}</p>
                  <p className="text-slate-400 text-sm">{formData.listing_type} / {formData.property_type}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Location</h4>
                  <p className="text-white">{formData.nearest_town || 'Not specified'}</p>
                  <p className="text-slate-400 text-sm">{formData.province_state}, {formData.country}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Property Size</h4>
                  <p className="text-white">{formData.total_claims || 0} claims</p>
                  <p className="text-slate-400 text-sm">{formData.total_hectares || 0} hectares</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Primary Mineral</h4>
                  <p className="text-white">{choices?.mineral_types?.find(m => m.value === formData.primary_mineral)?.label || formData.primary_mineral}</p>
                  <p className="text-slate-400 text-sm">{choices?.exploration_stages?.find(s => s.value === formData.exploration_stage)?.label}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Price</h4>
                  <p className="text-white">
                    {formData.asking_price
                      ? `${formData.price_currency} ${parseInt(formData.asking_price).toLocaleString()}`
                      : 'Contact for Price'}
                  </p>
                  {formData.open_to_offers && <p className="text-slate-400 text-sm">Open to offers</p>}
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Technical</h4>
                  <div className="flex flex-wrap gap-2">
                    {formData.has_43_101_report && <Badge variant="gold">NI 43-101</Badge>}
                    {formData.has_drilling && <Badge variant="copper">Drilling Data</Badge>}
                  </div>
                </div>
              </div>

              {formData.summary && (
                <div className="mt-6 pt-6 border-t border-slate-700">
                  <h4 className="text-sm font-medium text-gold-400 mb-2">Summary</h4>
                  <p className="text-slate-300">{formData.summary}</p>
                </div>
              )}
            </div>

            {error && (
              <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
                {error}
              </div>
            )}

            <div className="bg-gold-900/20 border border-gold-700/50 rounded-lg p-4">
              <p className="text-gold-300 text-sm">
                <strong>Note:</strong> Your listing will be reviewed before being published.
                You can upload images and documents after creating the listing.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">New Listing</Badge>
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8 overflow-x-auto pb-2">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <button
                onClick={() => setCurrentStep(step.id)}
                className={`flex flex-col items-center min-w-[80px] ${
                  step.id === currentStep
                    ? 'text-gold-400'
                    : step.id < currentStep
                    ? 'text-green-400'
                    : 'text-slate-500'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mb-1 ${
                    step.id === currentStep
                      ? 'bg-gold-600 text-white'
                      : step.id < currentStep
                      ? 'bg-green-600 text-white'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {step.id < currentStep ? '✓' : step.id}
                </div>
                <span className="text-xs whitespace-nowrap">{step.name}</span>
              </button>
              {index < STEPS.length - 1 && (
                <div className={`w-8 h-0.5 mx-1 ${step.id < currentStep ? 'bg-green-600' : 'bg-slate-700'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <Card className="p-6 md:p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">{STEPS[currentStep - 1].name}</h2>
            <p className="text-slate-400">{STEPS[currentStep - 1].description}</p>
          </div>

          {renderStepContent()}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-slate-700">
            <Button
              variant="ghost"
              onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
              disabled={currentStep === 1}
            >
              &larr; Previous
            </Button>

            <div className="flex gap-3">
              {currentStep === 8 ? (
                <>
                  <Button
                    variant="secondary"
                    onClick={() => handleSubmit(true)}
                    disabled={loading}
                  >
                    Save as Draft
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => handleSubmit(false)}
                    disabled={loading || !formData.title}
                  >
                    {loading ? 'Submitting...' : 'Submit Listing'}
                  </Button>
                </>
              ) : (
                <Button
                  variant="primary"
                  onClick={() => setCurrentStep(prev => Math.min(8, prev + 1))}
                >
                  Next &rarr;
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Commission Agreement Flow Component
function CommissionAgreementFlow({ onAccepted, accessToken }: { onAccepted: () => void; accessToken: string }) {
  const [agreementText, setAgreementText] = useState<string>('');
  const [commissionRate, setCommissionRate] = useState<string>('');
  const [version, setVersion] = useState<string>('');
  const [fullLegalName, setFullLegalName] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agreed, setAgreed] = useState(false);

  useEffect(() => {
    const fetchAgreement = async () => {
      try {
        const response = await fetch(`${API_URL}/properties/prospectors/agreement_text/`);
        if (response.ok) {
          const data = await response.json();
          setAgreementText(data.agreement_text);
          setCommissionRate(data.commission_rate);
          setVersion(data.version);
        }
      } catch (err) {
        console.error('Failed to fetch agreement:', err);
        setError('Failed to load agreement. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchAgreement();
  }, []);

  const handleAccept = async () => {
    if (!agreed || !fullLegalName.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/properties/prospectors/accept_agreement/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ full_legal_name: fullLegalName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Failed to accept agreement');
      }

      onAccepted();
    } catch (err) {
      console.error('Failed to accept agreement:', err);
      setError(err instanceof Error ? err.message : 'Failed to accept agreement');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <Card className="p-8">
          <div className="text-center mb-8">
            <Badge variant="gold" className="mb-4">Free Listing Agreement</Badge>
            <h1 className="text-3xl font-bold text-white mb-2">Prospector Commission Agreement</h1>
            <p className="text-slate-400">
              Please review and accept the following agreement to list your properties for free.
            </p>
          </div>

          <div className="bg-slate-800/50 rounded-lg p-6 mb-6 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <span className="text-sm text-slate-400">Version {version}</span>
              <Badge variant="copper">{commissionRate}% Commission</Badge>
            </div>
            <div className="prose prose-invert prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-slate-300 text-sm font-sans">
                {agreementText}
              </pre>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Full Legal Name (as signature)
              </label>
              <input
                type="text"
                value={fullLegalName}
                onChange={(e) => setFullLegalName(e.target.value)}
                placeholder="Enter your full legal name"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              />
            </div>

            <label className="flex items-start gap-3 cursor-pointer p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="w-5 h-5 mt-0.5 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
              />
              <div className="text-sm">
                <span className="text-white font-medium">I agree to the Commission Agreement</span>
                <p className="text-slate-400 mt-1">
                  By checking this box and entering my name above, I acknowledge that I have read,
                  understand, and agree to be bound by the terms of this Commission Agreement.
                </p>
              </div>
            </label>

            {error && (
              <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <Button
                variant="ghost"
                className="flex-1"
                onClick={() => window.location.href = '/properties'}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                className="flex-1"
                onClick={handleAccept}
                disabled={!agreed || !fullLegalName.trim() || submitting}
              >
                {submitting ? 'Processing...' : 'Accept & Continue'}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
