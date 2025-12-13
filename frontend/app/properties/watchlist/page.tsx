'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';
import { PropertyListingListItem } from '@/types/property';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface WatchlistItem {
  id: number;
  listing: PropertyListingListItem;
  notes: string;
  price_alert: boolean;
  added_at: string;
}

export default function WatchlistPage() {
  const router = useRouter();
  const { user, logout, accessToken, isLoading: authLoading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWatchlist = async () => {
      if (!accessToken) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/properties/watchlist/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch watchlist');
        }

        const data = await response.json();
        setWatchlist(Array.isArray(data) ? data : data.results || []);
      } catch (err) {
        console.error('Failed to fetch watchlist:', err);
        setError('Failed to load watchlist. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && accessToken) {
      fetchWatchlist();
    } else if (!authLoading && !accessToken) {
      setLoading(false);
    }
  }, [accessToken, authLoading]);

  const handleRemove = async (listingId: number) => {
    try {
      const response = await fetch(`${API_URL}/properties/watchlist/toggle/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ listing: listingId }),
      });

      if (response.ok) {
        setWatchlist(prev => prev.filter(item => item.listing.id !== listingId));
      }
    } catch (err) {
      console.error('Failed to remove from watchlist:', err);
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

  // Not logged in state
  if (!authLoading && !user) {
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
                <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>Properties</Button>
                <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>Login</Button>
                <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>Register</Button>
              </div>
            </div>
          </div>
        </nav>

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

        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <Card className="p-8 max-w-md mx-auto">
            <h1 className="text-2xl font-bold text-white mb-4">Sign In Required</h1>
            <p className="text-slate-300 mb-6">You need to be logged in to view your watchlist.</p>
            <Button variant="primary" onClick={() => setShowLogin(true)}>
              Sign In
            </Button>
          </Card>
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
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">My Watchlist</Badge>
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>
                Browse Exchange
              </Button>
              {user && (
                <>
                  <Button variant="ghost" size="sm" onClick={() => router.push('/properties/inbox')}>
                    Inbox
                  </Button>
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <section className="py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">My Watchlist</h1>
              <p className="text-slate-400">
                Properties you're tracking ({watchlist.length} {watchlist.length === 1 ? 'property' : 'properties'})
              </p>
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
          {!loading && !error && watchlist.length === 0 && (
            <Card className="p-12 text-center">
              <svg className="mx-auto h-16 w-16 text-slate-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              <h3 className="text-xl font-semibold text-white mb-2">Your watchlist is empty</h3>
              <p className="text-slate-400 mb-6 max-w-md mx-auto">
                Browse the Prospector's Exchange and save properties you're interested in to track them here.
              </p>
              <Button variant="primary" onClick={() => router.push('/properties')}>
                Browse Properties
              </Button>
            </Card>
          )}

          {/* Watchlist Grid */}
          {!loading && !error && watchlist.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {watchlist.map((item) => (
                <Card key={item.id} className="overflow-hidden hover:border-gold-500/50 transition-colors">
                  {/* Image */}
                  <div
                    className="relative h-48 bg-slate-800 cursor-pointer"
                    onClick={() => router.push(`/properties/${item.listing.slug}`)}
                  >
                    {item.listing.hero_image ? (
                      <img
                        src={item.listing.hero_image}
                        alt={item.listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-500">
                        <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </div>
                    )}

                    {/* Badges */}
                    <div className="absolute top-3 left-3 flex gap-2">
                      <Badge variant="gold">{item.listing.primary_mineral_display}</Badge>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3
                      className="text-lg font-semibold text-white mb-1 hover:text-gold-400 cursor-pointer truncate"
                      onClick={() => router.push(`/properties/${item.listing.slug}`)}
                    >
                      {item.listing.title}
                    </h3>
                    <p className="text-sm text-slate-400 mb-3">
                      {item.listing.province_state}, {item.listing.country_display}
                    </p>

                    <div className="grid grid-cols-2 gap-2 text-sm mb-4">
                      <div>
                        <span className="text-slate-500">Size:</span>
                        <span className="text-slate-300 ml-1">{item.listing.total_hectares?.toLocaleString() || 'N/A'} ha</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Stage:</span>
                        <span className="text-slate-300 ml-1">{item.listing.exploration_stage_display}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-slate-700">
                      <div className="text-gold-400 font-semibold">
                        {formatPrice(item.listing.asking_price, item.listing.price_currency)}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => router.push(`/properties/${item.listing.slug}`)}
                        >
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-400 hover:text-red-300"
                          onClick={() => handleRemove(item.listing.id)}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>

                    {/* Added date */}
                    <p className="text-xs text-slate-500 mt-3">
                      Added {new Date(item.added_at).toLocaleDateString()}
                    </p>
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
