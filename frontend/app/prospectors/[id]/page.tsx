'use client';

import { useState, useEffect, use } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProspectorProfile {
  id: number;
  username: string;
  email: string;
  display_name: string;
  company_name: string;
  bio: string;
  years_experience: number;
  specializations: string[];
  regions_active: string[];
  certifications: string[];
  website_url: string;
  phone: string;
  is_verified: boolean;
  verification_date: string | null;
  profile_image_url: string;
  total_listings: number;
  active_listings: number;
  successful_transactions: number;
  average_rating: number;
  listings_count: number;
  created_at: string;
}

interface PropertyListing {
  id: number;
  slug: string;
  title: string;
  primary_mineral: string;
  primary_mineral_display: string;
  country: string;
  country_display: string;
  state_province: string;
  asking_price: string;
  listing_type: string;
  listing_type_display: string;
  status: string;
  featured_image_url: string;
  acreage: string;
}

export default function ProspectorProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  const [profile, setProfile] = useState<ProspectorProfile | null>(null);
  const [listings, setListings] = useState<PropertyListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        // Fetch prospector profile
        const profileRes = await fetch(`${API_URL}/properties/prospectors/${resolvedParams.id}/`);
        if (!profileRes.ok) {
          if (profileRes.status === 404) {
            setError('Prospector not found');
          } else {
            setError('Failed to load profile');
          }
          return;
        }
        const profileData = await profileRes.json();
        setProfile(profileData);

        // Fetch prospector's active listings
        const listingsRes = await fetch(`${API_URL}/properties/listings/?prospector=${resolvedParams.id}&status=active`);
        if (listingsRes.ok) {
          const listingsData = await listingsRes.json();
          setListings(Array.isArray(listingsData) ? listingsData : listingsData.results || []);
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
        setError('Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [resolvedParams.id]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  if (error || !profile) {
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
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Properties</Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto py-16 px-4 text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Profile Not Found</h1>
          <p className="text-slate-400 mb-8">{error || 'The prospector profile you\'re looking for doesn\'t exist.'}</p>
          <Button variant="primary" onClick={() => window.location.href = '/properties'}>Browse Properties</Button>
        </div>
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
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Properties</Button>
              {user ? (
                <>
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties/inbox'}>Inbox</Button>
                  <span className="text-sm text-slate-300">Welcome, {user.full_name || user.username}</span>
                  <Button variant="ghost" size="sm" onClick={logout}>Logout</Button>
                </>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>Login</Button>
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>Register</Button>
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

      {/* Profile Header */}
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start gap-8">
            {/* Profile Image */}
            <div className="flex-shrink-0">
              {profile.profile_image_url ? (
                <img
                  src={profile.profile_image_url}
                  alt={profile.display_name}
                  className="w-32 h-32 rounded-full object-cover border-4 border-gold-500"
                />
              ) : (
                <div className="w-32 h-32 rounded-full bg-slate-700 flex items-center justify-center border-4 border-gold-500">
                  <span className="text-4xl text-slate-400">{profile.display_name[0]}</span>
                </div>
              )}
            </div>

            {/* Profile Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-white">{profile.display_name}</h1>
                {profile.is_verified && (
                  <Badge variant="gold">Verified</Badge>
                )}
              </div>
              {profile.company_name && (
                <p className="text-xl text-slate-300 mb-2">{profile.company_name}</p>
              )}
              <p className="text-slate-400 mb-4">
                {profile.years_experience} years of experience
                {profile.verification_date && ` • Verified since ${formatDate(profile.verification_date)}`}
              </p>

              {/* Stats */}
              <div className="flex flex-wrap gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gold-500">{profile.active_listings}</div>
                  <div className="text-sm text-slate-400">Active Listings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gold-500">{profile.total_listings}</div>
                  <div className="text-sm text-slate-400">Total Listings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gold-500">{profile.successful_transactions}</div>
                  <div className="text-sm text-slate-400">Transactions</div>
                </div>
                {profile.average_rating > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gold-500">{profile.average_rating.toFixed(1)}</div>
                    <div className="text-sm text-slate-400">Rating</div>
                  </div>
                )}
              </div>
            </div>

            {/* Contact */}
            <div className="flex flex-col gap-2">
              {profile.website_url && (
                <a
                  href={profile.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold-500 hover:text-gold-400 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  Website
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Bio & Details */}
          <div className="lg:col-span-1 space-y-6">
            {/* Bio */}
            {profile.bio && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">About</h3>
                <p className="text-slate-300 whitespace-pre-wrap">{profile.bio}</p>
              </Card>
            )}

            {/* Specializations */}
            {profile.specializations && profile.specializations.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Specializations</h3>
                <div className="flex flex-wrap gap-2">
                  {profile.specializations.map((spec, index) => (
                    <Badge key={index} variant="copper">{spec}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Regions */}
            {profile.regions_active && profile.regions_active.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Active Regions</h3>
                <div className="flex flex-wrap gap-2">
                  {profile.regions_active.map((region, index) => (
                    <Badge key={index} variant="slate">{region}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Certifications */}
            {profile.certifications && profile.certifications.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Certifications</h3>
                <ul className="space-y-2">
                  {profile.certifications.map((cert, index) => (
                    <li key={index} className="flex items-center gap-2 text-slate-300">
                      <svg className="w-4 h-4 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {cert}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Member Since */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-white mb-2">Member Since</h3>
              <p className="text-slate-300">{formatDate(profile.created_at)}</p>
            </Card>
          </div>

          {/* Right Column - Listings */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold text-white mb-6">
              Active Listings ({listings.length})
            </h2>

            {listings.length === 0 ? (
              <Card className="p-8 text-center">
                <p className="text-slate-400">No active listings at this time.</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {listings.map((listing) => (
                  <Card
                    key={listing.id}
                    className="overflow-hidden cursor-pointer hover:border-gold-500/50 transition-all"
                    onClick={() => window.location.href = `/properties/${listing.slug}`}
                  >
                    {/* Image */}
                    <div className="h-48 bg-slate-800 relative">
                      {listing.featured_image_url ? (
                        <img
                          src={listing.featured_image_url}
                          alt={listing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <svg className="w-16 h-16 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      )}
                      <div className="absolute top-3 left-3">
                        <Badge variant="gold">{listing.primary_mineral_display}</Badge>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="p-4">
                      <h3 className="font-semibold text-white mb-1 line-clamp-1">{listing.title}</h3>
                      <p className="text-sm text-slate-400 mb-2">
                        {listing.state_province && `${listing.state_province}, `}{listing.country_display}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-gold-500 font-semibold">
                          ${parseFloat(listing.asking_price).toLocaleString()}
                        </span>
                        <Badge variant="copper" className="text-xs">{listing.listing_type_display}</Badge>
                      </div>
                      {listing.acreage && (
                        <p className="text-xs text-slate-500 mt-2">
                          {parseFloat(listing.acreage).toLocaleString()} acres
                        </p>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
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
    </div>
  );
}
