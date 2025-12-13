'use client';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PropertyListingListItem } from '@/types/property';

interface PropertyCardProps {
  listing: PropertyListingListItem;
}

export function PropertyCard({ listing }: PropertyCardProps) {
  const formatPrice = (price: number | null, currency: string) => {
    if (!price) return 'Contact for Price';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'CAD',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getMineralColor = (mineral: string) => {
    const colors: Record<string, string> = {
      gold: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      silver: 'bg-slate-400/20 text-slate-300 border-slate-400/30',
      copper: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      lithium: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      uranium: 'bg-green-500/20 text-green-400 border-green-500/30',
      nickel: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
      zinc: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    };
    return colors[mineral] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  const getStatusBadge = (status: string) => {
    const statusStyles: Record<string, string> = {
      active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      under_contract: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      sold: 'bg-red-500/20 text-red-400 border-red-500/30',
      pending: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    };
    return statusStyles[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <Card
      className="group cursor-pointer hover:border-gold-500/50 transition-all duration-300 overflow-hidden"
      onClick={() => window.location.href = `/properties/${listing.slug}`}
    >
      {/* Image */}
      <div className="relative h-48 bg-slate-800 overflow-hidden">
        {listing.hero_image ? (
          <img
            src={listing.hero_image}
            alt={listing.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-slate-800">
            <svg className="w-16 h-16 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
        )}

        {/* Featured Badge */}
        {listing.is_featured && (
          <div className="absolute top-3 left-3">
            <Badge variant="gold" className="text-xs">Featured</Badge>
          </div>
        )}

        {/* Status Badge */}
        {listing.status !== 'active' && (
          <div className="absolute top-3 right-3">
            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusBadge(listing.status)}`}>
              {listing.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        )}

        {/* Mineral Type Badge */}
        <div className="absolute bottom-3 left-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getMineralColor(listing.primary_mineral)}`}>
            {listing.primary_mineral_display}
          </span>
        </div>

        {/* Watchlist indicator */}
        {listing.is_watchlisted && (
          <div className="absolute bottom-3 right-3">
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-red-500/80 text-white">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title & Location */}
        <h3 className="font-semibold text-white text-lg mb-1 line-clamp-1 group-hover:text-gold-400 transition-colors">
          {listing.title}
        </h3>
        <p className="text-sm text-slate-400 mb-3 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {listing.province_state}, {listing.country_display}
        </p>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
          <div className="flex items-center gap-1 text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            {formatNumber(listing.total_hectares)} ha
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            {listing.exploration_stage_display}
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            {formatNumber(listing.views_count)} views
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            {listing.listing_type_display}
          </div>
        </div>

        {/* Price & CTA */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-700">
          <div>
            <p className="text-lg font-bold text-gold-400">
              {formatPrice(listing.asking_price, listing.price_currency)}
            </p>
            {listing.open_to_offers && (
              <p className="text-xs text-emerald-400">Open to Offers</p>
            )}
          </div>
          <button className="px-4 py-2 bg-gold-600 hover:bg-gold-500 text-white text-sm font-medium rounded-lg transition-colors">
            View Details
          </button>
        </div>

        {/* Prospector */}
        <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between text-xs text-slate-500">
          <span>Listed by {listing.prospector_name}</span>
          <span>{new Date(listing.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </Card>
  );
}
