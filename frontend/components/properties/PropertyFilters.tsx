'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PropertyChoices, PropertySearchFilters } from '@/types/property';

interface PropertyFiltersProps {
  choices: PropertyChoices | null;
  filters: PropertySearchFilters;
  onFilterChange: (filters: PropertySearchFilters) => void;
  onClear: () => void;
}

export function PropertyFilters({ choices, filters, onFilterChange, onClear }: PropertyFiltersProps) {
  const [searchText, setSearchText] = useState(filters.search || '');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleChange = (key: keyof PropertySearchFilters, value: string | number | boolean | undefined) => {
    const newFilters = { ...filters };
    if (value === '' || value === undefined) {
      delete newFilters[key];
    } else {
      (newFilters as Record<string, unknown>)[key] = value;
    }
    onFilterChange(newFilters);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleChange('search', searchText || undefined);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.mineral) count++;
    if (filters.country) count++;
    if (filters.province) count++;
    if (filters.property_type) count++;
    if (filters.listing_type) count++;
    if (filters.stage) count++;
    if (filters.min_price || filters.max_price) count++;
    if (filters.min_size || filters.max_size) count++;
    if (filters.has_43_101) count++;
    if (filters.open_to_offers) count++;
    if (filters.search) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  // Get province options based on selected country
  const getProvinceOptions = () => {
    if (!choices) return [];
    switch (filters.country) {
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

  return (
    <Card className="sticky top-28">
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filters
            {activeCount > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-gold-600 text-white text-xs rounded-full">
                {activeCount}
              </span>
            )}
          </h3>
          {activeCount > 0 && (
            <button
              onClick={onClear}
              className="text-sm text-gold-400 hover:text-gold-300"
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Search</label>
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search properties..."
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
            <Button type="submit" variant="secondary" size="sm">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </Button>
          </form>
        </div>

        {/* Primary Mineral */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Mineral Type</label>
          <select
            value={filters.mineral || ''}
            onChange={(e) => handleChange('mineral', e.target.value || undefined)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
          >
            <option value="">All Minerals</option>
            {choices?.mineral_types?.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Country</label>
          <select
            value={filters.country || ''}
            onChange={(e) => {
              handleChange('country', e.target.value || undefined);
              handleChange('province', undefined); // Reset province when country changes
            }}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
          >
            <option value="">All Countries</option>
            {choices?.countries?.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {/* Province/State (conditional) */}
        {filters.country && getProvinceOptions().length > 0 && (
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              {filters.country === 'US' ? 'State' : 'Province'}
            </label>
            <select
              value={filters.province || ''}
              onChange={(e) => handleChange('province', e.target.value || undefined)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            >
              <option value="">All {filters.country === 'US' ? 'States' : 'Provinces'}</option>
              {getProvinceOptions().map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
        )}

        {/* Exploration Stage */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Exploration Stage</label>
          <select
            value={filters.stage || ''}
            onChange={(e) => handleChange('stage', e.target.value || undefined)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
          >
            <option value="">All Stages</option>
            {choices?.exploration_stages?.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {/* Show More Toggle */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-sm text-gold-400 hover:text-gold-300 flex items-center justify-center gap-1 py-2"
        >
          {isExpanded ? 'Show Less' : 'More Filters'}
          <svg className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Extended Filters */}
        {isExpanded && (
          <div className="space-y-4 pt-4 border-t border-slate-700">
            {/* Listing Type */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Listing Type</label>
              <select
                value={filters.listing_type || ''}
                onChange={(e) => handleChange('listing_type', e.target.value || undefined)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                {choices?.listing_types?.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            {/* Property Type */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Property Type</label>
              <select
                value={filters.property_type || ''}
                onChange={(e) => handleChange('property_type', e.target.value || undefined)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                {choices?.property_types?.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Price Range (CAD)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={filters.min_price || ''}
                  onChange={(e) => handleChange('min_price', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
                <input
                  type="number"
                  value={filters.max_price || ''}
                  onChange={(e) => handleChange('max_price', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Size Range */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Property Size (hectares)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={filters.min_size || ''}
                  onChange={(e) => handleChange('min_size', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
                <input
                  type="number"
                  value={filters.max_size || ''}
                  onChange={(e) => handleChange('max_size', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-1/2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Checkboxes */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.has_43_101 || false}
                  onChange={(e) => handleChange('has_43_101', e.target.checked ? true : undefined)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <span className="text-sm text-slate-300">Has NI 43-101 Report</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.open_to_offers || false}
                  onChange={(e) => handleChange('open_to_offers', e.target.checked ? true : undefined)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                />
                <span className="text-sm text-slate-300">Open to Offers</span>
              </label>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
