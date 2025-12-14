'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyListing } from '@/types/property';
import { InquiryForm } from '@/components/properties/InquiryForm';
import { ProfileEditModal } from '@/components/properties/ProfileEditModal';
import { ResourceUploadModal } from '@/components/properties/ResourceUploadModal';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PropertyDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showInquiryModal, setShowInquiryModal] = useState(false);
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [showResourceUpload, setShowResourceUpload] = useState(false);
  const { user, logout, accessToken } = useAuth();

  const [listing, setListing] = useState<PropertyListing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isWatchlisted, setIsWatchlisted] = useState(false);

  // Fetch listing
  useEffect(() => {
    const fetchListing = async () => {
      if (!slug) return;

      setLoading(true);
      setError(null);

      try {
        const headers: Record<string, string> = {};
        if (accessToken) {
          headers['Authorization'] = `Bearer ${accessToken}`;
        }

        const response = await fetch(`${API_URL}/properties/listings/${slug}/`, { headers });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Property not found');
          }
          throw new Error('Failed to fetch property');
        }

        const data = await response.json();
        setListing(data);
        setIsWatchlisted(data.is_watchlisted || false);
        setSelectedImage(data.hero_image || (data.media?.[0]?.file_url) || null);

        // Record view
        fetch(`${API_URL}/properties/listings/${slug}/record_view/`, {
          method: 'POST',
          headers,
        }).catch(console.error);
      } catch (err) {
        console.error('Failed to fetch listing:', err);
        setError(err instanceof Error ? err.message : 'Failed to load property');
      } finally {
        setLoading(false);
      }
    };

    fetchListing();
  }, [slug, accessToken]);

  const handleWatchlist = async () => {
    if (!user) {
      setShowLogin(true);
      return;
    }

    if (!listing) return;

    try {
      const response = await fetch(`${API_URL}/properties/watchlist/toggle/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ listing: listing.id }),
      });

      if (response.ok) {
        const data = await response.json();
        setIsWatchlisted(data.is_watchlisted);
        // Update the listing's watchlist count locally
        setListing(prev => prev ? { ...prev, watchlist_count: data.watchlist_count } : null);
      }
    } catch (err) {
      console.error('Failed to update watchlist:', err);
    }
  };

  const handleDelete = async () => {
    if (!user?.is_superuser) return;

    if (!confirm('Are you sure you want to permanently delete this listing? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/properties/listings/${slug}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        window.location.href = '/properties';
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to delete listing');
      }
    } catch (err) {
      console.error('Failed to delete listing:', err);
      alert('Failed to delete listing');
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

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center">
          <h1 className="text-2xl font-bold text-white mb-4">{error || 'Property Not Found'}</h1>
          <Button variant="primary" onClick={() => window.location.href = '/properties'}>
            Browse Prospector's Exchange
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
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.location.href = '/'}>
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>
                &larr; Back to Exchange
              </Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties/watchlist'}>
                    Watchlist
                  </Button>
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>
                    Login
                  </Button>
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Auth Modals */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => { setShowLogin(false); setShowRegister(true); }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => { setShowRegister(false); setShowLogin(true); }}
        />
      )}

      {/* Inquiry Modal */}
      {showInquiryModal && listing && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" onClick={() => setShowInquiryModal(false)}>
              <div className="absolute inset-0 bg-slate-900 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom sm:align-middle sm:max-w-lg sm:w-full relative">
              <button
                type="button"
                title="Close"
                aria-label="Close inquiry form"
                onClick={() => setShowInquiryModal(false)}
                className="absolute -top-2 -right-2 z-10 w-8 h-8 bg-slate-700 hover:bg-slate-600 rounded-full flex items-center justify-center text-slate-300"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <InquiryForm
                listingId={listing.id}
                listingTitle={listing.title}
                prospectorName={listing.prospector?.display_name || 'Prospector'}
                accessToken={accessToken}
                isAuthenticated={!!user}
                onLoginRequired={() => {
                  setShowInquiryModal(false);
                  setShowLogin(true);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <a href="/properties" className="hover:text-gold-400">Prospector's Exchange</a>
          <span>/</span>
          <span className="text-slate-300">{listing.title}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Images and Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Main Image */}
            <Card className="overflow-hidden">
              <div className="relative aspect-video bg-slate-800">
                {selectedImage ? (
                  <img
                    src={selectedImage}
                    alt={listing.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center">
                    <div className="w-20 h-20 rounded-full bg-slate-700/50 flex items-center justify-center mb-4">
                      <svg className="w-10 h-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-slate-300 mb-2">Property Images</h3>
                    <p className="text-sm text-slate-500 max-w-xs">
                      No images have been uploaded for this property yet. Check back soon for photos and maps of the project area.
                    </p>
                  </div>
                )}

                {/* Status Badge */}
                {listing.status !== 'active' && (
                  <div className="absolute top-4 right-4">
                    <Badge variant="copper">{listing.status.replace('_', ' ').toUpperCase()}</Badge>
                  </div>
                )}
              </div>

              {/* Thumbnail Gallery */}
              {listing.media && listing.media.length > 1 && (
                <div className="p-4 flex gap-2 overflow-x-auto">
                  {listing.media.filter(m => m.media_type === 'image').map((media) => (
                    <button
                      key={media.id}
                      onClick={() => setSelectedImage(media.file_url)}
                      className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-colors ${
                        selectedImage === media.file_url ? 'border-gold-500' : 'border-transparent hover:border-slate-600'
                      }`}
                    >
                      <img src={media.file_url} alt={media.title} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </Card>

            {/* Description */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Description</h2>
              <div className="prose prose-invert max-w-none">
                <p className="text-slate-300 whitespace-pre-wrap">{listing.description || listing.summary}</p>
              </div>

              {/* Investment Highlights */}
              {listing.investment_highlights && listing.investment_highlights.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-white mb-3">Investment Highlights</h3>
                  <ul className="space-y-2">
                    {listing.investment_highlights.map((highlight, i) => (
                      <li key={i} className="flex items-start gap-2 text-slate-300">
                        <svg className="w-5 h-5 text-gold-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {highlight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>

            {/* Technical Data */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Technical Data</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Geology */}
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Geology</h3>
                  <div className="space-y-4 text-sm">
                    <div className="grid grid-cols-[140px_1fr] gap-2">
                      <span className="text-slate-400">Deposit Type:</span>
                      <span className="text-white">{listing.deposit_type_display || 'N/A'}</span>
                    </div>
                    {listing.geological_setting && (
                      <div className="mt-4">
                        <h4 className="text-slate-400 text-xs uppercase tracking-wide mb-3">Geological Setting</h4>
                        <p className="text-white text-sm bg-slate-800/50 rounded-lg p-4 leading-relaxed whitespace-pre-wrap">{listing.geological_setting}</p>
                      </div>
                    )}
                    {listing.mineralization_style && (
                      <div className="mt-4">
                        <h4 className="text-slate-400 text-xs uppercase tracking-wide mb-3">Mineralization</h4>
                        <p className="text-white text-sm bg-slate-800/50 rounded-lg p-4 leading-relaxed whitespace-pre-wrap">{listing.mineralization_style}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Exploration */}
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Exploration Status</h3>
                  <div className="space-y-3 text-sm">
                    <div className="grid grid-cols-[140px_1fr] gap-2">
                      <span className="text-slate-400">Stage:</span>
                      <span className="text-white">{listing.exploration_stage_display}</span>
                    </div>
                    <div className="grid grid-cols-[140px_1fr] gap-2">
                      <span className="text-slate-400">Drilling:</span>
                      <span className="text-white">{listing.has_drilling ? `${formatNumber(listing.drill_hole_count)} holes / ${formatNumber(listing.total_meters_drilled)}m` : 'No'}</span>
                    </div>
                    <div className="grid grid-cols-[140px_1fr] gap-2">
                      <span className="text-slate-400">NI 43-101:</span>
                      <span className="text-white">{listing.has_43_101_report ? 'Yes' : 'No'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Assay Highlights */}
              {listing.assay_highlights && listing.assay_highlights.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Assay Highlights</h3>
                  <div className="bg-slate-800 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="px-4 py-2 text-left text-slate-400">Sample</th>
                          <th className="px-4 py-2 text-left text-slate-400">Mineral</th>
                          <th className="px-4 py-2 text-right text-slate-400">Grade</th>
                        </tr>
                      </thead>
                      <tbody>
                        {listing.assay_highlights.map((assay, i) => (
                          <tr key={i} className="border-b border-slate-700 last:border-0">
                            <td className="px-4 py-2 text-white">{assay.sample_id}</td>
                            <td className="px-4 py-2 text-white">{assay.mineral}</td>
                            <td className="px-4 py-2 text-right text-gold-400 font-medium">{assay.grade} {assay.unit}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </Card>

            {/* Resources & Documents */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Resources & Documents</h2>
                {listing.is_owner && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowResourceUpload(true)}
                  >
                    + Add Resource
                  </Button>
                )}
              </div>

              {/* Group resources by category */}
              {(() => {
                const resources = listing.media?.filter(m => m.media_type !== 'image' || m.category !== 'gallery') || [];
                const maps = resources.filter(r => ['geological_map', 'claim_map', 'location_map'].includes(r.category));
                const reports = resources.filter(r => ['report', 'assay'].includes(r.category));
                const permits = resources.filter(r => r.category === 'permit');
                const other = resources.filter(r => r.category === 'other');

                if (resources.length === 0) {
                  return (
                    <div className="text-center py-8">
                      <svg className="mx-auto w-12 h-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-slate-400">No resources uploaded yet</p>
                      {listing.is_owner && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2"
                          onClick={() => setShowResourceUpload(true)}
                        >
                          Upload your first resource
                        </Button>
                      )}
                    </div>
                  );
                }

                const ResourceSection = ({ title, icon, items }: { title: string; icon: string; items: typeof resources }) => {
                  if (items.length === 0) return null;
                  return (
                    <div className="mb-6 last:mb-0">
                      <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                        <span>{icon}</span> {title}
                      </h3>
                      <div className="space-y-2">
                        {items.map((resource) => (
                          <a
                            key={resource.id}
                            href={resource.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors group"
                          >
                            <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                              {resource.media_type === 'image' || resource.category.includes('map') ? (
                                <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                                </svg>
                              ) : (
                                <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-white font-medium truncate group-hover:text-gold-400 transition-colors">
                                {resource.title}
                              </p>
                              {resource.description && (
                                <p className="text-sm text-slate-400 truncate">{resource.description}</p>
                              )}
                              <p className="text-xs text-slate-500">
                                {resource.file_format?.toUpperCase()} {resource.file_size_mb && `• ${resource.file_size_mb} MB`}
                              </p>
                            </div>
                            <svg className="w-5 h-5 text-slate-500 group-hover:text-gold-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                };

                return (
                  <>
                    <ResourceSection title="Maps" icon="🗺️" items={maps} />
                    <ResourceSection title="Reports & Assays" icon="📊" items={reports} />
                    <ResourceSection title="Permits & Licenses" icon="📜" items={permits} />
                    <ResourceSection title="Other Documents" icon="📄" items={other} />
                  </>
                );
              })()}
            </Card>

            {/* Location & Infrastructure */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Location & Infrastructure</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Location</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Country:</span>
                      <span className="text-white">{listing.country_display}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Province/State:</span>
                      <span className="text-white">{listing.province_state}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Nearest Town:</span>
                      <span className="text-white">{listing.nearest_town || 'N/A'}</span>
                    </div>
                    {listing.coordinates_lat && listing.coordinates_lng && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">Coordinates:</span>
                        <span className="text-white">{listing.coordinates_lat}, {listing.coordinates_lng}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Infrastructure</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Road Access:</span>
                      <span className="text-white">{listing.road_access_display || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Power:</span>
                      <span className="text-white">{listing.power_available ? 'Available' : 'Not Available'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Water:</span>
                      <span className="text-white">{listing.water_available ? 'Available' : 'Not Available'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Camp:</span>
                      <span className="text-white">{listing.camp_infrastructure ? 'Yes' : 'No'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {listing.location_description && (
                <div className="mt-4 p-4 bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-300">{listing.location_description}</p>
                </div>
              )}
            </Card>
          </div>

          {/* Right Column - Pricing and Contact */}
          <div className="space-y-6">
            {/* Price Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Badge variant="gold">{listing.listing_type.replace('_', ' ').toUpperCase()}</Badge>
                {listing.is_featured && <Badge variant="copper">Featured</Badge>}
              </div>

              <h1 className="text-2xl font-bold text-white mb-2">{listing.title}</h1>
              <p className="text-slate-400 flex items-center gap-1 mb-4">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                {listing.province_state}, {listing.country_display}
              </p>

              <div className="border-t border-slate-700 pt-4">
                <p className="text-3xl font-bold text-gold-400 mb-2">
                  {formatPrice(listing.asking_price, listing.price_currency)}
                </p>
                {listing.open_to_offers && (
                  <p className="text-sm text-emerald-400 mb-4">Open to Offers</p>
                )}
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 py-4 border-t border-slate-700">
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{formatNumber(listing.total_hectares)}</p>
                  <p className="text-sm text-slate-400">Hectares</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{listing.total_claims || listing.claim_numbers?.length || 0}</p>
                  <p className="text-sm text-slate-400">Claims</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3 pt-4 border-t border-slate-700">
                {listing.is_owner ? (
                  /* Owner Actions */
                  <>
                    <Button
                      variant="primary"
                      size="lg"
                      className="w-full"
                      onClick={() => window.location.href = `/properties/${listing.slug}/edit`}
                    >
                      Edit Listing
                    </Button>
                    <Button
                      variant="secondary"
                      size="lg"
                      className="w-full"
                      onClick={() => window.location.href = '/properties/my-listings'}
                    >
                      My Listings
                    </Button>
                  </>
                ) : (
                  /* Visitor Actions */
                  <>
                    <Button
                      variant="primary"
                      size="lg"
                      className="w-full"
                      onClick={() => user ? setShowInquiryModal(true) : setShowLogin(true)}
                    >
                      Contact Prospector
                    </Button>
                    <Button
                      variant="secondary"
                      size="lg"
                      className="w-full"
                      onClick={handleWatchlist}
                    >
                      {isWatchlisted ? 'Remove from Watchlist' : 'Add to Watchlist'}
                    </Button>
                  </>
                )}

                {/* Admin Delete Button */}
                {user?.is_superuser && (
                  <Button
                    variant="ghost"
                    size="lg"
                    className="w-full text-red-400 hover:text-red-300 hover:bg-red-900/20"
                    onClick={handleDelete}
                  >
                    Delete Listing
                  </Button>
                )}
              </div>

              {/* Views */}
              <div className="mt-4 flex items-center justify-center gap-4 text-sm text-slate-400">
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {formatNumber(listing.views_count)} views
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  {formatNumber(listing.watchlist_count)} saved
                </span>
              </div>
            </Card>

            {/* Property Details */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Property Details</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Property Type:</span>
                  <span className="text-white">{listing.property_type.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Primary Mineral:</span>
                  <span className="text-white">{listing.primary_mineral_display}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Mineral Rights:</span>
                  <span className="text-white">{listing.mineral_rights_type_display}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Surface Rights:</span>
                  <span className="text-white">{listing.surface_rights_included ? 'Included' : 'Not Included'}</span>
                </div>
                {listing.nsr_royalty && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">NSR Royalty:</span>
                    <span className="text-white">{listing.nsr_royalty}%</span>
                  </div>
                )}
                {listing.expiry_date && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Claims Expiry:</span>
                    <span className="text-white">{new Date(listing.expiry_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Prospector Card */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Listed By</h3>
              <div className="flex items-start gap-4">
                {listing.prospector.profile_photo_url ? (
                  <img
                    src={listing.prospector.profile_photo_url}
                    alt={listing.prospector.display_name}
                    className="w-16 h-16 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-slate-700 flex items-center justify-center">
                    <span className="text-2xl text-slate-400">{listing.prospector.display_name[0]}</span>
                  </div>
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-white">{listing.prospector.display_name}</h4>
                  {listing.prospector.company_name && (
                    <p className="text-sm text-slate-400">{listing.prospector.company_name}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    {listing.prospector.is_verified && (
                      <Badge variant="gold" className="text-xs">Verified</Badge>
                    )}
                    <span className="text-xs text-slate-400">
                      {listing.prospector.years_experience} years experience
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700 space-y-2">
                {listing.is_owner ? (
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    onClick={() => setShowProfileEdit(true)}
                  >
                    Edit Profile
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="w-full"
                    onClick={() => window.location.href = `/prospectors/${listing.prospector.id}`}
                  >
                    View Profile
                  </Button>
                )}
              </div>
            </Card>

            {/* Claim Numbers */}
            {listing.claim_numbers && listing.claim_numbers.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Claim Numbers</h3>
                <div className="flex flex-wrap gap-2">
                  {listing.claim_numbers.map((claim, i) => (
                    <span key={i} className="px-2 py-1 bg-slate-800 rounded text-sm text-slate-300">
                      {claim}
                    </span>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>

      {/* Profile Edit Modal */}
      {showProfileEdit && listing && (
        <ProfileEditModal
          profileId={listing.prospector.id}
          onClose={() => setShowProfileEdit(false)}
          onSave={() => {
            // Refetch listing to get updated prospector data
            window.location.reload();
          }}
        />
      )}

      {/* Resource Upload Modal */}
      {showResourceUpload && listing && (
        <ResourceUploadModal
          listingId={listing.id}
          accessToken={accessToken}
          onClose={() => setShowResourceUpload(false)}
          onUploadComplete={() => {
            // Refetch listing to get updated media
            window.location.reload();
          }}
        />
      )}
    </div>
  );
}
