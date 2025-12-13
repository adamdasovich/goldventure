'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

interface PendingListing {
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
  hero_image: string | null;
  prospector_name: string;
  prospector_id: number;
  created_at: string;
}

export default function PropertyReviewPage() {
  const router = useRouter();
  const { user, accessToken, isLoading: authLoading } = useAuth();
  const [listings, setListings] = useState<PendingListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rejectingSlug, setRejectingSlug] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    if (!authLoading && accessToken) {
      fetchPendingListings();
    }
  }, [authLoading, accessToken]);

  const fetchPendingListings = async () => {
    try {
      const response = await fetch(`${API_URL}/properties/listings/pending/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setListings(data);
      } else if (response.status === 403) {
        setError('You do not have permission to view pending listings');
      } else {
        setError('Failed to fetch pending listings');
      }
    } catch (err) {
      console.error('Failed to fetch pending listings:', err);
      setError('Failed to fetch pending listings');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (slug: string) => {
    setActionLoading(slug);
    try {
      const response = await fetch(`${API_URL}/properties/listings/${slug}/approve/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        setListings(listings.filter(l => l.slug !== slug));
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to approve listing');
      }
    } catch (err) {
      console.error('Failed to approve listing:', err);
      alert('Failed to approve listing');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (slug: string) => {
    setActionLoading(slug);
    try {
      const response = await fetch(`${API_URL}/properties/listings/${slug}/reject/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: rejectReason }),
      });

      if (response.ok) {
        setListings(listings.filter(l => l.slug !== slug));
        setRejectingSlug(null);
        setRejectReason('');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to reject listing');
      }
    } catch (err) {
      console.error('Failed to reject listing:', err);
      alert('Failed to reject listing');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (slug: string) => {
    if (!confirm('Are you sure you want to permanently delete this listing? This cannot be undone.')) {
      return;
    }

    setActionLoading(slug);
    try {
      const response = await fetch(`${API_URL}/properties/listings/${slug}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        setListings(listings.filter(l => l.slug !== slug));
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to delete listing');
      }
    } catch (err) {
      console.error('Failed to delete listing:', err);
      alert('Failed to delete listing');
    } finally {
      setActionLoading(null);
    }
  };

  // Redirect if not logged in or not admin
  if (!authLoading && (!user || !user.is_superuser)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <h1 className="text-2xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-slate-300 mb-6">You need administrator access to view this page.</p>
          <Button variant="primary" onClick={() => router.push('/properties')}>
            Go to Properties
          </Button>
        </Card>
      </div>
    );
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
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
              <Badge variant="copper">Admin Review</Badge>
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>
                Back to Properties
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Pending Property Listings</h1>
          <p className="text-slate-400">
            Review and approve property listings submitted by prospectors
          </p>
        </div>

        {error && (
          <Card className="p-6 mb-6 bg-red-900/20 border-red-700">
            <p className="text-red-400">{error}</p>
          </Card>
        )}

        {listings.length === 0 ? (
          <Card className="p-12 text-center">
            <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-xl font-semibold text-white mb-2">No Pending Listings</h3>
            <p className="text-slate-400">All property listings have been reviewed.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {listings.map((listing) => (
              <Card key={listing.slug} className="p-6">
                <div className="flex flex-col md:flex-row gap-6">
                  {/* Listing Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-semibold text-white mb-1">
                          <a
                            href={`/properties/${listing.slug}`}
                            target="_blank"
                            className="hover:text-gold-400 transition-colors"
                          >
                            {listing.title}
                          </a>
                        </h3>
                        <p className="text-slate-400 text-sm">
                          Submitted by <span className="text-gold-400">{listing.prospector_name}</span>
                          {' '}&bull;{' '}
                          {new Date(listing.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge variant="copper">{listing.listing_type_display}</Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-slate-500 text-xs uppercase">Location</p>
                        <p className="text-white">{listing.province_state}, {listing.country_display}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs uppercase">Primary Mineral</p>
                        <p className="text-white">{listing.primary_mineral_display}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs uppercase">Size</p>
                        <p className="text-white">
                          {listing.total_hectares ? `${listing.total_hectares.toLocaleString()} ha` : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs uppercase">Price</p>
                        <p className="text-white">
                          {listing.asking_price
                            ? `${listing.price_currency} ${listing.asking_price.toLocaleString()}`
                            : 'Contact for Price'}
                        </p>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    {rejectingSlug === listing.slug ? (
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Rejection Reason (optional)
                        </label>
                        <textarea
                          value={rejectReason}
                          onChange={(e) => setRejectReason(e.target.value)}
                          placeholder="Provide a reason for rejection..."
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent mb-3"
                          rows={2}
                        />
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setRejectingSlug(null);
                              setRejectReason('');
                            }}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleReject(listing.slug)}
                            disabled={actionLoading === listing.slug}
                          >
                            {actionLoading === listing.slug ? 'Rejecting...' : 'Confirm Reject'}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex gap-3">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleApprove(listing.slug)}
                          disabled={actionLoading === listing.slug}
                        >
                          {actionLoading === listing.slug ? 'Approving...' : 'Approve'}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setRejectingSlug(listing.slug)}
                          disabled={actionLoading === listing.slug}
                        >
                          Reject
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(`/properties/${listing.slug}`, '_blank')}
                        >
                          View Details
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-400 hover:text-red-300"
                          onClick={() => handleDelete(listing.slug)}
                          disabled={actionLoading === listing.slug}
                        >
                          Delete
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Thumbnail */}
                  {listing.hero_image && (
                    <div className="w-full md:w-48 h-32 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0">
                      <img
                        src={listing.hero_image}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
