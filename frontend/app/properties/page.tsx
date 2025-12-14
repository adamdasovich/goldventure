'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyListingListItem, PropertyChoices, PropertySearchFilters } from '@/types/property';
import { PropertyCard } from '@/components/properties/PropertyCard';
import { PropertyFilters } from '@/components/properties/PropertyFilters';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PropertiesPage() {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout, accessToken } = useAuth();

  const [listings, setListings] = useState<PropertyListingListItem[]>([]);
  const [choices, setChoices] = useState<PropertyChoices | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<PropertySearchFilters>({
    sort: '-created_at'
  });

  // Fetch choices on mount
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

  // Fetch listings
  const fetchListings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (filters.mineral) params.append('mineral', filters.mineral);
      if (filters.country) params.append('country', filters.country);
      if (filters.province) params.append('province', filters.province);
      if (filters.property_type) params.append('property_type', filters.property_type);
      if (filters.listing_type) params.append('listing_type', filters.listing_type);
      if (filters.stage) params.append('stage', filters.stage);
      if (filters.min_price) params.append('min_price', filters.min_price.toString());
      if (filters.max_price) params.append('max_price', filters.max_price.toString());
      if (filters.min_size) params.append('min_size', filters.min_size.toString());
      if (filters.max_size) params.append('max_size', filters.max_size.toString());
      if (filters.has_43_101 !== undefined) params.append('has_43_101', filters.has_43_101.toString());
      if (filters.open_to_offers !== undefined) params.append('open_to_offers', filters.open_to_offers.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.sort) params.append('sort', filters.sort);

      const headers: Record<string, string> = {};
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      const response = await fetch(`${API_URL}/properties/listings/?${params}`, { headers });

      if (!response.ok) {
        throw new Error('Failed to fetch listings');
      }

      const data = await response.json();
      setListings(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Failed to fetch listings:', err);
      setError('Failed to load properties. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters, accessToken]);

  useEffect(() => {
    fetchListings();
  }, [fetchListings]);

  const handleFilterChange = (newFilters: PropertySearchFilters) => {
    setFilters(newFilters);
  };

  const clearFilters = () => {
    setFilters({ sort: '-created_at' });
  };

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
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Home</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/companies'}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/financial-hub'}>Financial Hub</Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    Welcome, {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties/watchlist'}>
                    Watchlist
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties/inbox'}>
                    Inbox
                  </Button>
                  {user.is_superuser && (
                    <Button variant="secondary" size="sm" onClick={() => window.location.href = '/properties/review'}>
                      Review Listings
                    </Button>
                  )}
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
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}

      {/* Hero Section */}
      <section className="relative py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Free Listings for Prospectors
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold animate-fade-in leading-tight pb-2">
            Prospector's Property Exchange
          </h1>
          <p className="text-lg text-slate-300 max-w-3xl mx-auto mb-8">
            Connect directly with prospectors. Browse mineral claims, exploration properties, and development projects across North America.
          </p>

          {user ? (
            <div className="flex flex-wrap gap-4 justify-center">
              <Button variant="primary" size="lg" onClick={() => window.location.href = '/properties/new'}>
                List Your Property
              </Button>
              <Button variant="secondary" size="lg" onClick={() => window.location.href = '/properties/my-listings'}>
                My Listings
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-4 justify-center">
              <Button variant="primary" size="lg" onClick={() => setShowRegister(true)}>
                Create Free Account
              </Button>
              <p className="text-sm text-slate-400 w-full mt-2">
                Prospectors: List unlimited properties for free
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Non-logged-in users see login prompt instead of listings */}
      {!user ? (
        <>
          {/* Login Prompt Section */}
          <section className="py-16 px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto text-center">
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8">
                <svg className="mx-auto h-16 w-16 text-gold-500 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <h2 className="text-2xl font-bold text-white mb-4">
                  Sign In to Browse Properties
                </h2>
                <p className="text-slate-400 mb-8">
                  Create a free account or sign in to browse available mineral properties, connect with prospectors, and manage your watchlist.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button variant="primary" size="lg" onClick={() => setShowRegister(true)}>
                    Create Free Account
                  </Button>
                  <Button variant="secondary" size="lg" onClick={() => setShowLogin(true)}>
                    Sign In
                  </Button>
                </div>
              </div>
            </div>
          </section>

          {/* CTA Section for non-logged-in users */}
          <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold text-white mb-4">
                Are You a Prospector?
              </h2>
              <p className="text-lg text-slate-300 mb-8">
                List your mineral properties for free on GoldVenture. Reach thousands of investors and mining companies looking for their next project.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Button variant="primary" size="lg" onClick={() => setShowRegister(true)}>
                  List Your Property
                </Button>
              </div>
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                <div className="bg-slate-900/50 p-6 rounded-lg">
                  <div className="text-gold-500 text-2xl mb-2">1.</div>
                  <h3 className="font-semibold text-white mb-2">Create Profile</h3>
                  <p className="text-sm text-slate-400">Set up your prospector profile with your credentials and experience.</p>
                </div>
                <div className="bg-slate-900/50 p-6 rounded-lg">
                  <div className="text-gold-500 text-2xl mb-2">2.</div>
                  <h3 className="font-semibold text-white mb-2">Add Your Properties</h3>
                  <p className="text-sm text-slate-400">Upload details, maps, assay results, and photos of your mineral claims.</p>
                </div>
                <div className="bg-slate-900/50 p-6 rounded-lg">
                  <div className="text-gold-500 text-2xl mb-2">3.</div>
                  <h3 className="font-semibold text-white mb-2">Connect with Buyers</h3>
                  <p className="text-sm text-slate-400">Receive inquiries directly from qualified investors and mining companies.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="py-8 px-4 border-t border-slate-800">
            <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
              <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
            </div>
          </footer>
        </>
      ) : (
        <>
      {/* Main Content - Only shown to logged-in users */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Filters Sidebar */}
            <aside className="lg:w-80 flex-shrink-0">
              <PropertyFilters
                choices={choices}
                filters={filters}
                onFilterChange={handleFilterChange}
                onClear={clearFilters}
              />
            </aside>

            {/* Listings Grid */}
            <main className="flex-1">
              {/* Results Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white">
                    {loading ? 'Loading...' : `${listings.length} Properties Found`}
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Sort by:</span>
                  <select
                    value={filters.sort || '-created_at'}
                    onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  >
                    <option value="-created_at">Newest First</option>
                    <option value="created_at">Oldest First</option>
                    <option value="-asking_price">Price: High to Low</option>
                    <option value="asking_price">Price: Low to High</option>
                    <option value="-total_hectares">Size: Large to Small</option>
                    <option value="total_hectares">Size: Small to Large</option>
                    <option value="-views_count">Most Viewed</option>
                  </select>
                </div>
              </div>

              {/* Error State */}
              {error && (
                <Card className="bg-red-900/20 border-red-700 mb-6">
                  <div className="p-4 text-red-400">{error}</div>
                </Card>
              )}

              {/* Loading State */}
              {loading && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[1, 2, 3, 4].map((i) => (
                    <Card key={i} className="animate-pulse">
                      <div className="h-48 bg-slate-700 rounded-t-lg"></div>
                      <div className="p-4 space-y-3">
                        <div className="h-4 bg-slate-700 rounded w-3/4"></div>
                        <div className="h-4 bg-slate-700 rounded w-1/2"></div>
                        <div className="h-4 bg-slate-700 rounded w-2/3"></div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {!loading && listings.length === 0 && (
                <Card className="text-center py-12">
                  <div className="text-slate-400">
                    <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <h3 className="text-lg font-medium text-white mb-2">No properties found</h3>
                    <p className="mb-4">Try adjusting your search filters or check back later for new listings.</p>
                    <Button variant="secondary" onClick={clearFilters}>Clear All Filters</Button>
                  </div>
                </Card>
              )}

              {/* Listings Grid */}
              {!loading && listings.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {listings.map((listing) => (
                    <PropertyCard key={listing.id} listing={listing} />
                  ))}
                </div>
              )}
            </main>
          </div>
        </div>
      </section>

      {/* CTA Section - for logged-in users */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Are You a Prospector?
          </h2>
          <p className="text-lg text-slate-300 mb-8">
            List your mineral properties for free on GoldVenture. Reach thousands of investors and mining companies looking for their next project.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Button variant="primary" size="lg" onClick={() => window.location.href = '/properties/new'}>
              List Your Property
            </Button>
          </div>
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="bg-slate-900/50 p-6 rounded-lg">
              <div className="text-gold-500 text-2xl mb-2">1.</div>
              <h3 className="font-semibold text-white mb-2">Create Profile</h3>
              <p className="text-sm text-slate-400">Set up your prospector profile with your credentials and experience.</p>
            </div>
            <div className="bg-slate-900/50 p-6 rounded-lg">
              <div className="text-gold-500 text-2xl mb-2">2.</div>
              <h3 className="font-semibold text-white mb-2">Add Your Properties</h3>
              <p className="text-sm text-slate-400">Upload details, maps, assay results, and photos of your mineral claims.</p>
            </div>
            <div className="bg-slate-900/50 p-6 rounded-lg">
              <div className="text-gold-500 text-2xl mb-2">3.</div>
              <h3 className="font-semibold text-white mb-2">Connect with Buyers</h3>
              <p className="text-sm text-slate-400">Receive inquiries directly from qualified investors and mining companies.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
        </>
      )}
    </div>
  );
}

