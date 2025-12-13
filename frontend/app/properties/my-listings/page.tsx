'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyListingListItem } from '@/types/property';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STATUS_BADGES: Record<string, { variant: 'gold' | 'copper' | 'slate'; label: string }> = {
  draft: { variant: 'slate', label: 'Draft' },
  pending: { variant: 'copper', label: 'Pending Review' },
  active: { variant: 'gold', label: 'Active' },
  under_contract: { variant: 'copper', label: 'Under Contract' },
  sold: { variant: 'slate', label: 'Sold' },
  withdrawn: { variant: 'slate', label: 'Withdrawn' },
};

export default function MyListingsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    }>
      <MyListingsContent />
    </Suspense>
  );
}

function MyListingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, accessToken, isLoading: authLoading } = useAuth();
  const [listings, setListings] = useState<PropertyListingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    totalViews: 0,
    totalInquiries: 0,
  });

  const createdSlug = searchParams.get('created');

  useEffect(() => {
    const fetchListings = async () => {
      if (!accessToken) return;

      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({ my_listings: 'true' });
        if (statusFilter !== 'all') {
          params.append('status', statusFilter);
        }

        const response = await fetch(`${API_URL}/properties/listings/?${params}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch listings');
        }

        const data = await response.json();
        const listingsData = Array.isArray(data) ? data : data.results || [];
        setListings(listingsData);

        // Calculate stats
        const active = listingsData.filter((l: PropertyListingListItem) => l.status === 'active').length;
        const totalViews = listingsData.reduce((sum: number, l: PropertyListingListItem) => sum + (l.views_count || 0), 0);
        setStats({
          total: listingsData.length,
          active,
          totalViews,
          totalInquiries: 0, // Would need separate API call
        });
      } catch (err) {
        console.error('Failed to fetch listings:', err);
        setError('Failed to load your listings. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && accessToken) {
      fetchListings();
    } else if (!authLoading && !accessToken) {
      setLoading(false);
    }
  }, [accessToken, authLoading, statusFilter]);

  const handleDeleteListing = async (slug: string) => {
    if (!confirm('Are you sure you want to delete this listing? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/properties/listings/${slug}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete listing');
      }

      setListings(prev => prev.filter(l => l.slug !== slug));
    } catch (err) {
      console.error('Failed to delete listing:', err);
      alert('Failed to delete listing. Please try again.');
    }
  };

  const formatPrice = (price: number | null, currency: string) => {
    if (!price) return 'Contact for Price';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'CAD',
      maximumFractionDigits: 0,
    }).format(price);
  };

  // Redirect if not logged in
  if (!authLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <h1 className="text-2xl font-bold text-white mb-4">Sign In Required</h1>
          <p className="text-slate-300 mb-6">You need to be logged in to view your listings.</p>
          <Button variant="primary" onClick={() => router.push('/properties')}>
            Go to Prospector's Exchange
          </Button>
        </Card>
      </div>
    );
  }

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
              <Badge variant="copper">My Listings</Badge>
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>
                Browse Exchange
              </Button>
              <Button variant="primary" size="sm" onClick={() => router.push('/properties/new')}>
                + New Listing
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Success Banner */}
      {createdSlug && (
        <div className="bg-green-900/30 border-b border-green-700">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-green-300">Your listing has been created successfully!</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/properties/${createdSlug}`)}
            >
              View Listing
            </Button>
          </div>
        </div>
      )}

      {/* Stats Section */}
      <section className="py-8 px-4 border-b border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4 text-center">
              <div className="text-3xl font-bold text-gold-400">{stats.total}</div>
              <div className="text-sm text-slate-400">Total Listings</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-3xl font-bold text-green-400">{stats.active}</div>
              <div className="text-sm text-slate-400">Active Listings</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-3xl font-bold text-blue-400">{stats.totalViews}</div>
              <div className="text-sm text-slate-400">Total Views</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-3xl font-bold text-purple-400">{stats.totalInquiries}</div>
              <div className="text-sm text-slate-400">Inquiries</div>
            </Card>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <h1 className="text-2xl font-bold text-white">My Property Listings</h1>

            <div className="flex items-center gap-3">
              <label htmlFor="status-filter" className="text-sm text-slate-400">Filter:</label>
              <select
                id="status-filter"
                title="Filter by status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="draft">Drafts</option>
                <option value="pending">Pending Review</option>
                <option value="active">Active</option>
                <option value="under_contract">Under Contract</option>
                <option value="sold">Sold</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <Card className="bg-red-900/20 border-red-700 p-6 text-center">
              <p className="text-red-400">{error}</p>
              <Button variant="secondary" className="mt-4" onClick={() => window.location.reload()}>
                Try Again
              </Button>
            </Card>
          )}

          {/* Empty State */}
          {!loading && !error && listings.length === 0 && (
            <Card className="p-12 text-center">
              <svg className="mx-auto h-16 w-16 text-slate-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="text-xl font-semibold text-white mb-2">No listings yet</h3>
              <p className="text-slate-400 mb-6 max-w-md mx-auto">
                Start listing your mineral properties for free. Reach thousands of investors and mining companies.
              </p>
              <Button variant="primary" onClick={() => router.push('/properties/new')}>
                Create Your First Listing
              </Button>
            </Card>
          )}

          {/* Listings Table */}
          {!loading && !error && listings.length > 0 && (
            <div className="space-y-4">
              {listings.map((listing) => (
                <Card key={listing.id} className="p-4 md:p-6">
                  <div className="flex flex-col md:flex-row gap-4">
                    {/* Image */}
                    <div className="w-full md:w-48 h-32 bg-slate-800 rounded-lg overflow-hidden flex-shrink-0">
                      {listing.hero_image ? (
                        <img
                          src={listing.hero_image}
                          alt={listing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-500">
                          <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-white truncate">
                            {listing.title}
                          </h3>
                          <p className="text-sm text-slate-400">
                            {listing.province_state}, {listing.country_display}
                          </p>
                        </div>
                        <Badge variant={STATUS_BADGES[listing.status]?.variant || 'slate'}>
                          {STATUS_BADGES[listing.status]?.label || listing.status}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                        <div>
                          <span className="text-slate-500">Type:</span>
                          <span className="text-slate-300 ml-2">{listing.listing_type_display}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Mineral:</span>
                          <span className="text-slate-300 ml-2">{listing.primary_mineral_display}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Size:</span>
                          <span className="text-slate-300 ml-2">{listing.total_hectares?.toLocaleString() || 'N/A'} ha</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Price:</span>
                          <span className="text-gold-400 ml-2">{formatPrice(listing.asking_price, listing.price_currency)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            {listing.views_count || 0} views
                          </span>
                          <span className="text-slate-600">|</span>
                          <span>Created {new Date(listing.created_at).toLocaleDateString()}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => router.push(`/properties/${listing.slug}`)}
                          >
                            View
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => router.push(`/properties/${listing.slug}/edit`)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-400 hover:text-red-300"
                            onClick={() => handleDeleteListing(listing.slug)}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
