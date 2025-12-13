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

interface DashboardStats {
  totalListings: number;
  activeListings: number;
  totalViews: number;
  totalInquiries: number;
  pendingInquiries: number;
  watchlistCount: number;
}

interface RecentInquiry {
  id: number;
  listing_title: string;
  listing_slug: string;
  inquiry_type_display: string;
  status: string;
  status_display: string;
  subject: string;
  created_at: string;
  is_received: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, accessToken, isLoading: authLoading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  const [stats, setStats] = useState<DashboardStats>({
    totalListings: 0,
    activeListings: 0,
    totalViews: 0,
    totalInquiries: 0,
    pendingInquiries: 0,
    watchlistCount: 0,
  });
  const [recentListings, setRecentListings] = useState<PropertyListingListItem[]>([]);
  const [recentInquiries, setRecentInquiries] = useState<RecentInquiry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!accessToken) return;

      setLoading(true);

      try {
        // Fetch user's listings
        const listingsRes = await fetch(`${API_URL}/properties/listings/?my_listings=true`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const listingsData = listingsRes.ok ? await listingsRes.json() : [];
        const listings = Array.isArray(listingsData) ? listingsData : listingsData.results || [];

        // Fetch watchlist
        const watchlistRes = await fetch(`${API_URL}/properties/watchlist/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const watchlistData = watchlistRes.ok ? await watchlistRes.json() : [];
        const watchlist = Array.isArray(watchlistData) ? watchlistData : watchlistData.results || [];

        // Fetch inquiries
        const inquiriesRes = await fetch(`${API_URL}/properties/inquiries/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const inquiriesData = inquiriesRes.ok ? await inquiriesRes.json() : [];
        const inquiries = Array.isArray(inquiriesData) ? inquiriesData : inquiriesData.results || [];

        // Calculate stats
        const activeListings = listings.filter((l: PropertyListingListItem) => l.status === 'active').length;
        const totalViews = listings.reduce((sum: number, l: PropertyListingListItem) => sum + (l.views_count || 0), 0);
        const pendingInquiries = inquiries.filter((i: RecentInquiry) => i.status === 'new' || i.status === 'read').length;

        setStats({
          totalListings: listings.length,
          activeListings,
          totalViews,
          totalInquiries: inquiries.length,
          pendingInquiries,
          watchlistCount: watchlist.length,
        });

        // Set recent listings (last 5)
        setRecentListings(listings.slice(0, 5));

        // Set recent inquiries (last 5)
        setRecentInquiries(inquiries.slice(0, 5).map((i: any) => ({
          id: i.id,
          listing_title: i.listing?.title || 'Unknown Listing',
          listing_slug: i.listing?.slug || '',
          inquiry_type_display: i.inquiry_type_display || i.inquiry_type,
          status: i.status,
          status_display: i.status_display || i.status,
          subject: i.subject,
          created_at: i.created_at,
          is_received: i.listing?.prospector_id === user?.id,
        })));

      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && accessToken) {
      fetchDashboardData();
    } else if (!authLoading && !accessToken) {
      setLoading(false);
    }
  }, [accessToken, authLoading, user?.id]);

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
            <p className="text-slate-300 mb-6">You need to be logged in to view your dashboard.</p>
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
              <Button variant="ghost" size="sm" onClick={() => router.push('/properties')}>Properties</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/metals')}>Metals</Button>
              {user && (
                <>
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
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name || user?.username}
          </h1>
          <p className="text-slate-400">
            Here's an overview of your activity on GoldVenture
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
          </div>
        )}

        {!loading && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              <Card className="p-4 text-center hover:border-gold-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/my-listings')}>
                <div className="text-3xl font-bold text-gold-400">{stats.totalListings}</div>
                <div className="text-sm text-slate-400">Total Listings</div>
              </Card>
              <Card className="p-4 text-center hover:border-green-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/my-listings')}>
                <div className="text-3xl font-bold text-green-400">{stats.activeListings}</div>
                <div className="text-sm text-slate-400">Active Listings</div>
              </Card>
              <Card className="p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{stats.totalViews}</div>
                <div className="text-sm text-slate-400">Total Views</div>
              </Card>
              <Card className="p-4 text-center hover:border-purple-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/inbox')}>
                <div className="text-3xl font-bold text-purple-400">{stats.totalInquiries}</div>
                <div className="text-sm text-slate-400">Inquiries</div>
              </Card>
              <Card className="p-4 text-center hover:border-orange-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/inbox')}>
                <div className="text-3xl font-bold text-orange-400">{stats.pendingInquiries}</div>
                <div className="text-sm text-slate-400">Pending</div>
              </Card>
              <Card className="p-4 text-center hover:border-pink-500/50 transition-colors cursor-pointer" onClick={() => router.push('/properties/watchlist')}>
                <div className="text-3xl font-bold text-pink-400">{stats.watchlistCount}</div>
                <div className="text-sm text-slate-400">Watchlist</div>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="p-6 mb-8">
              <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
              <div className="flex flex-wrap gap-3">
                <Button variant="primary" onClick={() => router.push('/properties/new')}>
                  + Create New Listing
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/my-listings')}>
                  Manage My Listings
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/inbox')}>
                  View Inbox
                </Button>
                <Button variant="secondary" onClick={() => router.push('/properties/watchlist')}>
                  My Watchlist
                </Button>
                <Button variant="ghost" onClick={() => router.push('/properties')}>
                  Browse Properties
                </Button>
              </div>
            </Card>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Listings */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">My Recent Listings</h2>
                  <Button variant="ghost" size="sm" onClick={() => router.push('/properties/my-listings')}>
                    View All
                  </Button>
                </div>

                {recentListings.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-slate-400 mb-4">You haven't created any listings yet.</p>
                    <Button variant="primary" size="sm" onClick={() => router.push('/properties/new')}>
                      Create Your First Listing
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentListings.map((listing) => (
                      <div
                        key={listing.id}
                        className="flex items-center gap-4 p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 cursor-pointer transition-colors"
                        onClick={() => router.push(`/properties/${listing.slug}`)}
                      >
                        <div className="w-16 h-16 rounded-lg bg-slate-700 overflow-hidden flex-shrink-0">
                          {listing.hero_image ? (
                            <img src={listing.hero_image} alt={listing.title} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-500">
                              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-white font-medium truncate">{listing.title}</h3>
                          <p className="text-sm text-slate-400">{listing.province_state}, {listing.country_display}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant={listing.status === 'active' ? 'gold' : 'slate'} className="text-xs">
                              {listing.status}
                            </Badge>
                            <span className="text-xs text-slate-500">{listing.views_count || 0} views</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-gold-400 font-semibold text-sm">
                            {formatPrice(listing.asking_price, listing.price_currency)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Recent Inquiries */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">Recent Inquiries</h2>
                  <Button variant="ghost" size="sm" onClick={() => router.push('/properties/inbox')}>
                    View All
                  </Button>
                </div>

                {recentInquiries.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-slate-400">No inquiries yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentInquiries.map((inquiry) => (
                      <div
                        key={inquiry.id}
                        className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 cursor-pointer transition-colors"
                        onClick={() => router.push('/properties/inbox')}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-white font-medium truncate">{inquiry.subject}</h3>
                            <p className="text-sm text-slate-400 truncate">
                              Re: {inquiry.listing_title}
                            </p>
                          </div>
                          <Badge
                            variant={inquiry.status === 'new' ? 'gold' : inquiry.status === 'responded' ? 'slate' : 'copper'}
                            className="text-xs flex-shrink-0"
                          >
                            {inquiry.status_display}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                          <span>{inquiry.inquiry_type_display}</span>
                          <span>•</span>
                          <span>{new Date(inquiry.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* Admin Section */}
            {user?.is_superuser && (
              <Card className="p-6 mt-8 border-gold-500/30">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-gold-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Admin Actions
                </h2>
                <div className="flex flex-wrap gap-3">
                  <Button variant="secondary" onClick={() => router.push('/properties/review')}>
                    Review Pending Listings
                  </Button>
                </div>
              </Card>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
